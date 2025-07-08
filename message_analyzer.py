"""
AI-powered message analyzer for relocation status detection
Analyzes messages to determine open/closed status with confidence scoring
"""

import re
import asyncio
from typing import Dict, Any, List, Tuple
from datetime import datetime
from logger import setup_logger

class MessageAnalyzer:
    def __init__(self):
        self.logger = setup_logger()
        
        # Keywords and patterns for status detection
        self.open_keywords = [
            'open', 'opened', 'available', 'free', 'vacant', 'working',
            'відкрито', 'відкритий', 'доступно', 'працює', 'вільно',
            'работает', 'открыто', 'доступно', 'свободно'
        ]
        
        self.closed_keywords = [
            'closed', 'close', 'unavailable', 'blocked', 'not working',
            'закрито', 'закритий', 'недоступно', 'не працює', 'заблоковано',
            'закрыто', 'не работает', 'недоступно', 'заблокировано'
        ]
        
        # Time-based patterns
        self.time_patterns = [
            r'\b(\d{1,2}):(\d{2})\b',  # HH:MM format
            r'\b(\d{1,2})\s*(год|час|hour|h)\b',  # Hour mentions
            r'\b(сьогодні|today|вчора|yesterday|завтра|tomorrow)\b'  # Day mentions
        ]
        
        # Status indicators
        self.status_indicators = [
            r'статус[:\s]*([а-яё\w\s]+)',  # Status: ...
            r'стан[:\s]*([а-яё\w\s]+)',   # State: ...
            r'status[:\s]*([a-z\w\s]+)',   # Status: ...
            r'состояние[:\s]*([а-яё\w\s]+)'  # State: ...
        ]
        
    async def analyze_message(self, text: str) -> Dict[str, Any]:
        """
        Analyze message text to determine relocation status
        Returns analysis with suggested status and confidence
        """
        try:
            text_lower = text.lower()
            
            # Initialize analysis result
            analysis = {
                'suggested_status': 'unknown',
                'confidence': 0.0,
                'keywords_found': [],
                'time_mentioned': False,
                'status_indicators': [],
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            # Score for open/closed detection
            open_score = 0
            closed_score = 0
            
            # Check for open keywords
            for keyword in self.open_keywords:
                if keyword in text_lower:
                    open_score += 1
                    analysis['keywords_found'].append(('open', keyword))
                    
            # Check for closed keywords
            for keyword in self.closed_keywords:
                if keyword in text_lower:
                    closed_score += 1
                    analysis['keywords_found'].append(('closed', keyword))
                    
            # Check for time patterns
            for pattern in self.time_patterns:
                if re.search(pattern, text_lower):
                    analysis['time_mentioned'] = True
                    break
                    
            # Check for status indicators
            for pattern in self.status_indicators:
                matches = re.findall(pattern, text_lower)
                if matches:
                    analysis['status_indicators'].extend(matches)
                    
            # Advanced pattern analysis
            context_score = await self.analyze_context(text_lower)
            open_score += context_score['open']
            closed_score += context_score['closed']
            
            # Determine final status and confidence
            if open_score > closed_score:
                analysis['suggested_status'] = 'open'
                analysis['confidence'] = min(open_score / (open_score + closed_score + 1), 0.95)
            elif closed_score > open_score:
                analysis['suggested_status'] = 'closed'
                analysis['confidence'] = min(closed_score / (open_score + closed_score + 1), 0.95)
            else:
                analysis['suggested_status'] = 'unknown'
                analysis['confidence'] = 0.1
                
            # Boost confidence if time is mentioned
            if analysis['time_mentioned']:
                analysis['confidence'] = min(analysis['confidence'] + 0.1, 0.98)
                
            # Boost confidence if status indicators are present
            if analysis['status_indicators']:
                analysis['confidence'] = min(analysis['confidence'] + 0.15, 0.98)
                
            self.logger.debug(f"Message analysis: {analysis}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing message: {e}")
            return {
                'suggested_status': 'unknown',
                'confidence': 0.0,
                'keywords_found': [],
                'time_mentioned': False,
                'status_indicators': [],
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
            
    async def analyze_context(self, text: str) -> Dict[str, int]:
        """
        Analyze message context for additional scoring
        """
        context_score = {'open': 0, 'closed': 0}
        
        # Positive context patterns (indicating open)
        positive_patterns = [
            r'можна\s+(проїхати|пройти|попасти)',  # Can pass/go through
            r'(проїзд|прохід)\s+(вільний|можливий)',  # Passage is free/possible
            r'(робота|працює|функціонує)',  # Working/functioning
            r'(available|accessible|passable)',  # English positive
        ]
        
        # Negative context patterns (indicating closed)
        negative_patterns = [
            r'(не\s+можна|неможливо|заборонено)',  # Cannot/impossible/forbidden
            r'(заблокован|перекрит|закрыт)',  # Blocked/closed
            r'(не\s+працює|не\s+робить)',  # Not working
            r'(blocked|closed|unavailable)',  # English negative
        ]
        
        # Check positive patterns
        for pattern in positive_patterns:
            if re.search(pattern, text):
                context_score['open'] += 1
                
        # Check negative patterns
        for pattern in negative_patterns:
            if re.search(pattern, text):
                context_score['closed'] += 1
                
        # Check for urgency indicators
        urgency_patterns = [
            r'(терміново|urgent|срочно)',  # Urgent
            r'(зараз|now|сейчас)',  # Now
            r'(негайно|immediately|немедленно)'  # Immediately
        ]
        
        for pattern in urgency_patterns:
            if re.search(pattern, text):
                # Urgency typically indicates status change
                context_score['open'] += 0.5
                context_score['closed'] += 0.5
                
        return context_score
        
    def get_analysis_summary(self, analysis: Dict[str, Any]) -> str:
        """
        Generate human-readable analysis summary
        """
        status = analysis['suggested_status']
        confidence = analysis['confidence']
        keywords = analysis['keywords_found']
        
        summary = f"Status: {status.upper()} (Confidence: {confidence:.1%})\n"
        
        if keywords:
            summary += f"Keywords found: {', '.join([kw[1] for kw in keywords])}\n"
            
        if analysis['time_mentioned']:
            summary += "Time information detected\n"
            
        if analysis['status_indicators']:
            summary += f"Status indicators: {', '.join(analysis['status_indicators'])}\n"
            
        return summary
        
    async def batch_analyze(self, messages: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple messages in batch
        """
        tasks = [self.analyze_message(msg) for msg in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Batch analysis error: {result}")
                valid_results.append({
                    'suggested_status': 'unknown',
                    'confidence': 0.0,
                    'keywords_found': [],
                    'time_mentioned': False,
                    'status_indicators': [],
                    'analysis_timestamp': datetime.utcnow().isoformat(),
                    'error': str(result)
                })
            else:
                valid_results.append(result)
                
        return valid_results
