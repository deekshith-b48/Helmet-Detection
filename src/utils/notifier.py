"""
Notification system for Helmet Detection System.
Handles email notifications, fine generation, and notification tracking.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import time
import threading
from queue import Queue

logger = logging.getLogger(__name__)

class EmailTemplate:
    """Email template manager"""
    
    @staticmethod
    def violation_notice(violation_data: Dict) -> str:
        """Generate violation notice email content"""
        return f"""
        Traffic Violation Notice
        
        Date: {violation_data['timestamp']}
        License Plate: {violation_data['license_plate']}
        Violation Type: {violation_data['violation_type']}
        Fine Amount: ${violation_data['fine_amount']}
        
        Please pay the fine within 30 days to avoid additional penalties.
        Payment can be made online at: https://traffic.gov/pay-fine
        
        This is an automated message. Do not reply to this email.
        """
    
    @staticmethod
    def fine_receipt(payment_data: Dict) -> str:
        """Generate fine payment receipt email content"""
        return f"""
        Payment Receipt - Traffic Violation Fine
        
        Transaction ID: {payment_data['transaction_id']}
        Date: {payment_data['payment_date']}
        Amount Paid: ${payment_data['amount']}
        Payment Method: {payment_data['payment_method']}
        
        Thank you for your payment.
        """

class NotificationManager:
    """Handles all notification operations"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.email_config = config['email']
        self.notification_queue = Queue()
        self.retry_delays = [5, 15, 30]  # Retry delays in seconds
        self.templates = EmailTemplate()
        
        # Start notification worker thread
        self.worker_thread = threading.Thread(target=self._process_notification_queue)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
    def send_violation_notice(self, 
                            violation_data: Dict, 
                            image_path: Optional[str] = None) -> bool:
        """Send violation notice email"""
        try:
            # Prepare email
            msg = MIMEMultipart()
            msg['From'] = self.email_config['SENDER_EMAIL']
            msg['To'] = violation_data['owner_email']
            msg['Subject'] = f"Traffic Violation Notice - {violation_data['license_plate']}"
            
            # Add email body
            body = self.templates.violation_notice(violation_data)
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach violation image if available
            if image_path and Path(image_path).exists():
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', '<violation_image>')
                    msg.attach(img)
            
            # Queue notification for sending
            self.notification_queue.put({
                'msg': msg,
                'recipient': violation_data['owner_email'],
                'type': 'violation_notice',
                'retry_count': 0
            })
            
            logger.info(f"Violation notice queued for {violation_data['license_plate']}")
            return True
            
        except Exception as e:
            logger.error(f"Error preparing violation notice: {e}")
            return False
            
    def send_batch_notifications(self, violations: List[Dict]) -> Dict:
        """Send notifications for multiple violations"""
        results = {
            'success': 0,
            'failed': 0,
            'queued': len(violations)
        }
        
        for violation in violations:
            try:
                if self.send_violation_notice(violation):
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"Error in batch notification: {e}")
                results['failed'] += 1
                
        return results
        
    def _process_notification_queue(self):
        """Process notifications in the queue"""
        while True:
            try:
                if not self.notification_queue.empty():
                    notification = self.notification_queue.get()
                    success = self._send_email(notification['msg'])
                    
                    if not success and notification['retry_count'] < len(self.retry_delays):
                        # Schedule retry
                        retry_delay = self.retry_delays[notification['retry_count']]
                        notification['retry_count'] += 1
                        time.sleep(retry_delay)
                        self.notification_queue.put(notification)
                    
                time.sleep(1)  # Prevent busy waiting
                
            except Exception as e:
                logger.error(f"Error processing notification queue: {e}")
                time.sleep(5)  # Wait before retrying
                
    def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email using SMTP"""
        try:
            with smtplib.SMTP(self.email_config['SMTP_SERVER'], 
                            self.email_config['SMTP_PORT']) as server:
                server.starttls()
                server.login(
                    self.email_config['SENDER_EMAIL'],
                    self.email_config['SENDER_PASSWORD']
                )
                server.send_message(msg)
                logger.info(f"Email sent successfully to {msg['To']}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
            
    def send_fine_receipt(self, payment_data: Dict) -> bool:
        """Send fine payment receipt"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['SENDER_EMAIL']
            msg['To'] = payment_data['email']
            msg['Subject'] = f"Payment Receipt - Traffic Violation Fine"
            
            body = self.templates.fine_receipt(payment_data)
            msg.attach(MIMEText(body, 'plain'))
            
            self.notification_queue.put({
                'msg': msg,
                'recipient': payment_data['email'],
                'type': 'fine_receipt',
                'retry_count': 0
            })
            
            logger.info(f"Fine receipt queued for {payment_data['transaction_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error preparing fine receipt: {e}")
            return False
            
    def get_notification_stats(self) -> Dict:
        """Get notification statistics"""
        return {
            'queue_size': self.notification_queue.qsize(),
            'notifications_sent': self._get_sent_count(),
            'failed_notifications': self._get_failed_count()
        }
        
    def _get_sent_count(self) -> int:
        """Get count of successfully sent notifications"""
        # Implementation depends on your tracking mechanism
        return 0
        
    def _get_failed_count(self) -> int:
        """Get count of failed notifications"""
        # Implementation depends on your tracking mechanism
        return 0