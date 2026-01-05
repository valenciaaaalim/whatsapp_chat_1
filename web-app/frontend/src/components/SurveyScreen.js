import React, { useState } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import axios from 'axios';
import './SurveyScreen.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Pre-study survey questions (both variants) - 4 Likert items about confidence and familiarity
const PRE_SURVEY_QUESTIONS = [
  {
    id: 'pre_1',
    question: 'How confident are you in identifying potential privacy risks in online conversations?',
    type: 'likert',
    scale: 5
  },
  {
    id: 'pre_2',
    question: 'How familiar are you with privacy warnings in messaging applications?',
    type: 'likert',
    scale: 5
  },
  {
    id: 'pre_3',
    question: 'How confident are you in protecting your personal information online?',
    type: 'likert',
    scale: 5
  },
  {
    id: 'pre_4',
    question: 'How familiar are you with social engineering attacks?',
    type: 'likert',
    scale: 5
  }
];

// Variant A mid-survey questions (3 questions per conversation)
const MID_SURVEY_A_QUESTIONS = [
  {
    id: 'midA_q1',
    question: 'The warning was clear.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'midA_q2',
    question: 'The warning helped me notice something new.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'midA_q3',
    question: 'The suggested rewrite preserved what I wanted to say.',
    type: 'likert',
    scale: 5
  }
];

// Variant B mid-survey questions (2 questions per conversation)
const MID_SURVEY_B_QUESTIONS = [
  {
    id: 'midB_q1',
    question: 'Which type of personal information did you end up disclosing?',
    type: 'multiple_choice',
    options: ['Name', 'Email address', 'Phone number', 'Address', 'Financial information', 'Other', 'None']
  },
  {
    id: 'midB_q2',
    question: 'How likely is it that the other person was malicious?',
    type: 'scale',
    scale: 5,
    labels: ['Very unlikely', 'Unlikely', 'Neutral', 'Likely', 'Very likely']
  }
];

// Post-survey: SUS questions (Variant A only)
const SUS_QUESTIONS = [
  {
    id: 'sus_1',
    question: 'I think that I would like to use this system frequently.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'sus_2',
    question: 'I found the system unnecessarily complex.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'sus_3',
    question: 'I thought the system was easy to use.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'sus_4',
    question: 'I think that I would need the support of a technical person to be able to use this system.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'sus_5',
    question: 'I found the various functions in this system were well integrated.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'sus_6',
    question: 'I thought there was too much inconsistency in this system.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'sus_7',
    question: 'I would imagine that most people would learn to use this system very quickly.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'sus_8',
    question: 'I found the system very cumbersome to use.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'sus_9',
    question: 'I felt very confident using the system.',
    type: 'likert',
    scale: 5
  },
  {
    id: 'sus_10',
    question: 'I needed to learn a lot of things before I could get going with this system.',
    type: 'likert',
    scale: 5
  }
];

// Post-survey extra questions (Variant A only)
const POST_EXTRA_QUESTIONS = [
  {
    id: 'post_trust',
    question: 'Overall, I trusted the information presented by the system/interface.',
    type: 'scale',
    scale: 7,
    labels: ['1', '2', '3', '4', '5', '6', '7']
  },
  {
    id: 'post_realism',
    question: 'Overall, the study tasks felt realistic.',
    type: 'scale',
    scale: 5,
    labels: ['1', '2', '3', '4', '5']
  }
];

function SurveyScreen({ participantId, participantProlificId, variant }) {
  const navigate = useNavigate();
  const params = useParams();
  const [searchParams] = useSearchParams();
  const surveyType = params.type || 'mid';
  const conversationIndex = searchParams.get('index');
  
  // Determine which questions to show based on survey type and variant
  let questions = [];
  if (surveyType === 'pre') {
    questions = PRE_SURVEY_QUESTIONS;
  } else if (surveyType === 'mid') {
    questions = variant === 'A' ? MID_SURVEY_A_QUESTIONS : MID_SURVEY_B_QUESTIONS;
  } else if (surveyType === 'post') {
    // Post-survey includes SUS questions + 2 extra questions
    questions = [...SUS_QUESTIONS, ...POST_EXTRA_QUESTIONS];
  }
  
  const [responses, setResponses] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const surveyInstance =
    surveyType === 'mid' && conversationIndex !== null
      ? `${surveyType}_${conversationIndex}`
      : surveyType;

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
      // Submit all responses to survey_responses table
      await Promise.all(
        Object.entries(responses).map(([questionId, response]) => {
          const question = questions.find(q => q.id === questionId);
          return axios.post(`${API_BASE_URL}/api/surveys/responses`, {
            survey_type: surveyInstance,
            question_id: questionId,
            question_text: question.question,
            response_text: typeof response === 'string' ? response : null,
            response_json: typeof response === 'object' ? response : null
          }, {
            params: { participant_id: participantId }
          });
        })
      );

      // Submit to participant_records table based on survey type
      if (surveyType === 'pre') {
        const answers = questions.map(q => responses[q.id]);
        await axios.post(`${API_BASE_URL}/api/participant-records/pre-survey`, {
          participant_id: participantProlificId,
          answers,
          variant
        });
      } else if (surveyType === 'mid') {
        const convIndex = parseInt(conversationIndex || '0', 10);
        if (variant === 'A') {
          await axios.post(`${API_BASE_URL}/api/participant-records/mid-survey-a`, {
            participant_id: participantProlificId,
            conversation_index: convIndex,
            q1: responses['midA_q1'],
            q2: responses['midA_q2'],
            q3: responses['midA_q3'],
            variant
          });
        } else {
          await axios.post(`${API_BASE_URL}/api/participant-records/mid-survey-b`, {
            participant_id: participantProlificId,
            conversation_index: convIndex,
            q1: responses['midB_q1'],
            q2: responses['midB_q2'],
            variant
          });
        }
      } else if (surveyType === 'post') {
        // SUS questions
        const susAnswers = SUS_QUESTIONS.map(q => responses[q.id]);
        await axios.post(`${API_BASE_URL}/api/participant-records/sus`, {
          participant_id: participantProlificId,
          answers: susAnswers,
          variant
        });
        // Extra questions
        await axios.post(`${API_BASE_URL}/api/participant-records/post-extra`, {
          participant_id: participantProlificId,
          trust: responses['post_trust'],
          realism: responses['post_realism'],
          variant
        });
      }

      // Navigate based on survey type
      if (surveyType === 'pre') {
        navigate('/conversation/0');
      } else if (surveyType === 'mid') {
        const nextIndex = parseInt(conversationIndex || '0') + 1;
        if (nextIndex < 3) {
          navigate(`/conversation/${nextIndex}`);
        } else {
          // After 3rd conversation mid-survey
          if (variant === 'A') {
            navigate('/survey/post');
          } else {
            // Variant B goes directly to completion
            navigate('/completion');
          }
        }
      } else {
        // Post-survey (Variant A only)
        navigate('/completion');
      }
    } catch (error) {
      console.error('Error submitting survey:', error);
      alert('Error submitting survey. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderQuestion = (question) => {
    if (question.type === 'likert') {
      const labels = ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree'];
      return (
        <div className="rating-options">
          {Array.from({ length: question.scale }, (_, i) => {
            const value = i + 1;
            const label = labels[i] || value;
            return (
              <button
                key={i}
                className={`rating-option ${
                  responses[question.id] === value.toString() ? 'selected' : ''
                }`}
                onClick={() => handleResponse(question.id, value.toString())}
              >
                <div>{value}</div>
                <div className="option-label">{label}</div>
              </button>
            );
          })}
        </div>
      );
    } else if (question.type === 'scale') {
      const labels = question.labels || Array.from({ length: question.scale }, (_, i) => (i + 1).toString());
      return (
        <div className="rating-options">
          {Array.from({ length: question.scale }, (_, i) => {
            const value = i + 1;
            const label = labels[i] || value;
            return (
              <button
                key={i}
                className={`rating-option ${
                  responses[question.id] === value.toString() ? 'selected' : ''
                }`}
                onClick={() => handleResponse(question.id, value.toString())}
              >
                <div>{value}</div>
                {label.length <= 3 && <div className="option-label">{label}</div>}
              </button>
            );
          })}
        </div>
      );
    } else if (question.type === 'multiple_choice') {
      return (
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
      );
    }
    return null;
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
              {renderQuestion(question)}
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
