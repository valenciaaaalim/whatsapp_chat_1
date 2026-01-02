import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import './SurveyScreen.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const SURVEY_QUESTIONS = {
  mid: [
    {
      id: 'mid_1',
      question: 'How clear were the privacy warnings you encountered?',
      type: 'rating',
      options: ['Very unclear', 'Somewhat unclear', 'Neutral', 'Somewhat clear', 'Very clear']
    },
    {
      id: 'mid_2',
      question: 'Did the warnings influence your messaging decisions?',
      type: 'multiple_choice',
      options: ['Yes, significantly', 'Yes, somewhat', 'No, not really', 'No, not at all']
    }
  ],
  post: [
    {
      id: 'post_1',
      question: 'Overall, how helpful were the privacy warnings?',
      type: 'rating',
      options: ['Not helpful', 'Slightly helpful', 'Moderately helpful', 'Very helpful', 'Extremely helpful']
    },
    {
      id: 'post_2',
      question: 'Would you want similar warnings in real messaging apps?',
      type: 'multiple_choice',
      options: ['Definitely yes', 'Probably yes', 'Maybe', 'Probably no', 'Definitely no']
    }
  ]
};

function SurveyScreen({ participantId }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const surveyType = searchParams.get('type') || 'mid';
  const conversationIndex = searchParams.get('index');
  
  const questions = SURVEY_QUESTIONS[surveyType] || SURVEY_QUESTIONS.mid;
  const [responses, setResponses] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const handleResponse = (questionId, response) => {
    setResponses({ ...responses, [questionId]: response });
  };

  const handleSubmit = async () => {
    if (Object.keys(responses).length !== questions.length) {
      alert('Please answer all questions');
      return;
    }

    setSubmitting(true);
    try {
      // Submit all responses
      await Promise.all(
        Object.entries(responses).map(([questionId, response]) => {
          const question = questions.find(q => q.id === questionId);
          return axios.post(`${API_BASE_URL}/api/surveys/responses`, {
            survey_type: surveyType,
            question_id: questionId,
            question_text: question.question,
            response_text: typeof response === 'string' ? response : null,
            response_json: typeof response === 'object' ? response : null
          }, {
            params: { participant_id: participantId }
          });
        })
      );

      // Navigate based on survey type
      if (surveyType === 'mid') {
        const nextIndex = parseInt(conversationIndex || '0') + 1;
        navigate(`/conversation/${nextIndex}`);
      } else {
        navigate('/completion');
      }
    } catch (error) {
      console.error('Error submitting survey:', error);
      alert('Error submitting survey. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="survey-screen">
      <div className="survey-content">
        <h1>Survey Questions</h1>
        <p>Please answer the following questions about your experience.</p>
        
        <div className="survey-questions">
          {questions.map((question) => (
            <div key={question.id} className="survey-question">
              <label className="question-label">{question.question}</label>
              {question.type === 'rating' && (
                <div className="rating-options">
                  {question.options.map((option, idx) => (
                    <button
                      key={idx}
                      className={`rating-option ${
                        responses[question.id] === option ? 'selected' : ''
                      }`}
                      onClick={() => handleResponse(question.id, option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              )}
              {question.type === 'multiple_choice' && (
                <div className="multiple-choice-options">
                  {question.options.map((option, idx) => (
                    <label key={idx} className="multiple-choice-option">
                      <input
                        type="radio"
                        name={question.id}
                        value={option}
                        checked={responses[question.id] === option}
                        onChange={() => handleResponse(question.id, option)}
                      />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        
        <button
          className="submit-button"
          onClick={handleSubmit}
          disabled={submitting || Object.keys(responses).length !== questions.length}
        >
          {submitting ? 'Submitting...' : 'Continue'}
        </button>
      </div>
    </div>
  );
}

export default SurveyScreen;

