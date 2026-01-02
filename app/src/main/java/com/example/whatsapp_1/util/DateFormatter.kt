package com.example.whatsapp_1.util

import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

object DateFormatter {
    private val dateFormat = SimpleDateFormat("MMM d, yyyy", Locale.getDefault())
    
    fun formatDateSeparator(date: Date): String {
        val dateCalendar = Calendar.getInstance().apply {
            time = date
        }
        val today = Calendar.getInstance()
        val yesterday = Calendar.getInstance().apply {
            add(Calendar.DAY_OF_YEAR, -1)
        }
        
        return when {
            isSameDay(dateCalendar, today) -> "Today"
            isSameDay(dateCalendar, yesterday) -> "Yesterday"
            else -> dateFormat.format(date)
        }
    }
    
    fun formatTime(date: Date): String {
        val format = SimpleDateFormat("h:mm a", Locale.getDefault())
        return format.format(date)
    }
    
    private fun isSameDay(cal1: Calendar, cal2: Calendar): Boolean {
        return cal1.get(Calendar.YEAR) == cal2.get(Calendar.YEAR) &&
                cal1.get(Calendar.DAY_OF_YEAR) == cal2.get(Calendar.DAY_OF_YEAR)
    }
    
    fun needsDateSeparator(prevDate: Date?, currentDate: Date): Boolean {
        if (prevDate == null) return true
        
        val prevCal = Calendar.getInstance().apply { time = prevDate }
        val currentCal = Calendar.getInstance().apply { time = currentDate }
        
        return !isSameDay(prevCal, currentCal)
    }
}

