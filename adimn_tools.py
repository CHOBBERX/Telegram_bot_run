#!/usr/bin/env python3
"""
Advanced Admin Tools for Telegram Bot
Provides comprehensive administrative utilities and management functions
"""

import sqlite3
import datetime
import json
import csv
import logging
import os
from typing import Dict, List, Optional, Tuple
from config import DATABASE_FILE

logger = logging.getLogger(__name__)

class AdminToolkit:
    """Comprehensive admin toolkit for bot management"""
    
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
    
    def get_database_connection(self):
        """Get database connection with error handling"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def get_user_analytics(self, days: int = 30) -> Dict:
        """Get comprehensive user analytics"""
        conn = self.get_database_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Basic user stats
            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            total_users = cursor.fetchone()['total_users']
            
            cursor.execute("SELECT COUNT(*) as active_users FROM users WHERE is_active = TRUE")
            active_users = cursor.fetchone()['active_users']
            
            # New users in period
            cursor.execute("""
                SELECT COUNT(*) as new_users 
                FROM users 
                WHERE DATE(joined_on) >= DATE('now', '-' || ? || ' days')
            """, (days,))
            new_users = cursor.fetchone()['new_users']
            
            # Top users by tokens
            cursor.execute("""
                SELECT id, username, first_name, tokens, redemptions 
                FROM users 
                ORDER BY tokens DESC 
                LIMIT 10
            """)
            top_token_users = [dict(row) for row in cursor.fetchall()]
            
            # Top users by redemptions
            cursor.execute("""
                SELECT id, username, first_name, tokens, redemptions 
                FROM users 
                ORDER BY redemptions DESC 
                LIMIT 10
            """)
            top_redemption_users = [dict(row) for row in cursor.fetchall()]
            
            # Daily active users trend
            cursor.execute("""
                SELECT DATE(last_activity) as date, COUNT(*) as active_users
                FROM users 
                WHERE DATE(last_activity) >= DATE('now', '-' || ? || ' days')
                GROUP BY DATE(last_activity)
                ORDER BY date DESC
            """, (days,))
            daily_activity = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'new_users': new_users,
                'top_token_users': top_token_users,
                'top_redemption_users': top_redemption_users,
                'daily_activity': daily_activity,
                'analysis_period': days
            }
            
        except Exception as e:
            logger.error(f"User analytics error: {e}")
            conn.close()
            return {}
    
    def get_content_analytics(self) -> Dict:
        """Get content performance analytics"""
        conn = self.get_database_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Basic content stats
            cursor.execute("SELECT COUNT(*) as total_content FROM content WHERE is_active = TRUE")
            total_content = cursor.fetchone()['total_content']
            
            cursor.execute("SELECT SUM(views) as total_views FROM content WHERE is_active = TRUE")
            total_views = cursor.fetchone()['total_views'] or 0
            
            cursor.execute("SELECT AVG(views) as avg_views FROM content WHERE is_active = TRUE")
            avg_views = cursor.fetchone()['avg_views'] or 0
            
            # Content by type
            cursor.execute("""
                SELECT file_type, COUNT(*) as count, SUM(views) as total_views
                FROM content 
                WHERE is_active = TRUE
                GROUP BY file_type
            """)
            content_by_type = [dict(row) for row in cursor.fetchall()]
            
            # Top performing content
            cursor.execute("""
                SELECT id, caption, views, file_type, uploaded_on
                FROM content 
                WHERE is_active = TRUE
                ORDER BY views DESC 
                LIMIT 10
            """)
            top_content = [dict(row) for row in cursor.fetchall()]
            
            # Recent uploads
            cursor.execute("""
                SELECT id, caption, views, file_type, uploaded_on, uploaded_by
                FROM content 
                WHERE is_active = TRUE
                ORDER BY uploaded_on DESC 
                LIMIT 10
            """)
            recent_uploads = [dict(row) for row in cursor.fetchall()]
            
            # Content performance by category
            cursor.execute("""
                SELECT category, COUNT(*) as count, SUM(views) as total_views, AVG(views) as avg_views
                FROM content 
                WHERE is_active = TRUE
                GROUP BY category
                ORDER BY total_views DESC
            """)
            category_performance = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_content': total_content,
                'total_views': total_views,
                'avg_views': round(avg_views, 2),
                'content_by_type': content_by_type,
                'top_content': top_content,
                'recent_uploads': recent_uploads,
                'category_performance': category_performance
            }
            
        except Exception as e:
            logger.error(f"Content analytics error: {e}")
            conn.close()
            return {}
    
    def get_financial_analytics(self) -> Dict:
        """Get token economy and financial analytics"""
        conn = self.get_database_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Token distribution
            cursor.execute("SELECT SUM(tokens) as total_tokens FROM users")
            total_tokens_in_system = cursor.fetchone()['total_tokens'] or 0
            
            # Transaction analytics
            cursor.execute("""
                SELECT transaction_type, COUNT(*) as count, SUM(amount) as total_amount
                FROM token_transactions
                GROUP BY transaction_type
            """)
            transaction_summary = [dict(row) for row in cursor.fetchall()]
            
            # Daily transaction volume
            cursor.execute("""
                SELECT DATE(timestamp) as date, 
                       COUNT(*) as transaction_count,
                       SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as tokens_added,
                       SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as tokens_spent
                FROM token_transactions
                WHERE DATE(timestamp) >= DATE('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """)
            daily_transactions = [dict(row) for row in cursor.fetchall()]
            
            # Revenue estimation (assuming token prices)
            cursor.execute("""
                SELECT SUM(amount) as total_purchased
                FROM token_transactions
                WHERE transaction_type IN ('purchase', 'admin_add')
            """)
            estimated_revenue_tokens = cursor.fetchone()['total_purchased'] or 0
            
            # Top spenders
            cursor.execute("""
                SELECT u.id, u.username, u.first_name, 
                       SUM(CASE WHEN tt.amount < 0 THEN ABS(tt.amount) ELSE 0 END) as tokens_spent
                FROM users u
                JOIN token_transactions tt ON u.id = tt.user_id
                WHERE tt.transaction_type = 'redeem'
                GROUP BY u.id
                ORDER BY tokens_spent DESC
                LIMIT 10
            """)
            top_spenders = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_tokens_in_system': total_tokens_in_system,
                'transaction_summary': transaction_summary,
                'daily_transactions': daily_transactions,
                'estimated_revenue_tokens': estimated_revenue_tokens,
                'estimated_revenue_inr': estimated_revenue_tokens * 10,  # Assuming ₹10 per token average
                'top_spenders': top_spenders
            }
            
        except Exception as e:
            logger.error(f"Financial analytics error: {e}")
            conn.close()
            return {}
    
    def get_referral_analytics(self) -> Dict:
        """Get referral program analytics"""
        conn = self.get_database_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Basic referral stats
            cursor.execute("SELECT COUNT(*) as total_referrals FROM referrals")
            total_referrals = cursor.fetchone()['total_referrals']
            
            cursor.execute("SELECT SUM(bonus_amount) as total_bonuses FROM referrals")
            total_bonuses = cursor.fetchone()['total_bonuses'] or 0
            
            # Top referrers
            cursor.execute("""
                SELECT u.id, u.username, u.first_name,
                       COUNT(r.id) as referral_count,
                       SUM(r.bonus_amount) as total_earned
                FROM users u
                JOIN referrals r ON u.id = r.referrer_id
                GROUP BY u.id
                ORDER BY referral_count DESC
                LIMIT 10
            """)
            top_referrers = [dict(row) for row in cursor.fetchall()]
            
            # Referral conversion rate
            cursor.execute("SELECT COUNT(DISTINCT referrer_id) as active_referrers FROM referrals")
            active_referrers = cursor.fetchone()['active_referrers']
            
            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            total_users = cursor.fetchone()['total_users']
            
            referral_participation_rate = (active_referrers / total_users * 100) if total_users > 0 else 0
            
            # Daily referral activity
            cursor.execute("""
                SELECT DATE(referred_on) as date, COUNT(*) as referrals
                FROM referrals
                WHERE DATE(referred_on) >= DATE('now', '-30 days')
                GROUP BY DATE(referred_on)
                ORDER BY date DESC
            """)
            daily_referrals = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_referrals': total_referrals,
                'total_bonuses': total_bonuses,
                'top_referrers': top_referrers,
                'active_referrers': active_referrers,
                'referral_participation_rate': round(referral_participation_rate, 2),
                'daily_referrals': daily_referrals
            }
            
        except Exception as e:
            logger.error(f"Referral analytics error: {e}")
            conn.close()
            return {}
    
    def export_user_data(self, output_file: str = None) -> str:
        """Export user data to CSV"""
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"users_export_{timestamp}.csv"
        
        conn = self.get_database_connection()
        if not conn:
            return ""
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, first_name, last_name, tokens, redemptions, 
                       referral_by, joined_on, is_active, total_spent
                FROM users
                ORDER BY joined_on DESC
            """)
            
            users = cursor.fetchall()
            conn.close()
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'username', 'first_name', 'last_name', 'tokens', 
                            'redemptions', 'referral_by', 'joined_on', 'is_active', 'total_spent']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for user in users:
                    writer.writerow(dict(user))
            
            logger.info(f"User data exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"User export error: {e}")
            conn.close()
            return ""
    
    def export_content_data(self, output_file: str = None) -> str:
        """Export content data to CSV"""
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"content_export_{timestamp}.csv"
        
        conn = self.get_database_connection()
        if not conn:
            return ""
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, file_id, file_type, caption, category, views, 
                       uploaded_by, uploaded_on, is_active
                FROM content
                ORDER BY uploaded_on DESC
            """)
            
            content = cursor.fetchall()
            conn.close()
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'file_id', 'file_type', 'caption', 'category', 
                            'views', 'uploaded_by', 'uploaded_on', 'is_active']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for item in content:
                    writer.writerow(dict(item))
            
            logger.info(f"Content data exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Content export error: {e}")
            conn.close()
            return ""
    
    def generate_admin_report(self, output_file: str = None) -> str:
        """Generate comprehensive admin report"""
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"admin_report_{timestamp}.json"
        
        try:
            report = {
                'generated_at': datetime.datetime.now().isoformat(),
                'user_analytics': self.get_user_analytics(),
                'content_analytics': self.get_content_analytics(),
                'financial_analytics': self.get_financial_analytics(),
                'referral_analytics': self.get_referral_analytics()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Admin report generated: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return ""
    
    def cleanup_inactive_users(self, days: int = 90) -> int:
        """Remove inactive users after specified days"""
        conn = self.get_database_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            
            # Find inactive users
            cursor.execute("""
                SELECT id FROM users 
                WHERE last_activity < datetime('now', '-' || ? || ' days')
                AND tokens = 0 
                AND redemptions = 0
            """, (days,))
            
            inactive_users = cursor.fetchall()
            inactive_count = len(inactive_users)
            
            if inactive_count > 0:
                # Delete related data first (due to foreign keys)
                for user in inactive_users:
                    user_id = user['id']
                    cursor.execute("DELETE FROM referrals WHERE referrer_id = ? OR referred_id = ?", (user_id, user_id))
                    cursor.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
                    cursor.execute("DELETE FROM token_transactions WHERE user_id = ?", (user_id,))
                    cursor.execute("DELETE FROM logs WHERE user_id = ?", (user_id,))
                
                # Delete users
                cursor.execute("""
                    DELETE FROM users 
                    WHERE last_activity < datetime('now', '-' || ? || ' days')
                    AND tokens = 0 
                    AND redemptions = 0
                """, (days,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {inactive_count} inactive users")
            return inactive_count
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            conn.close()
            return 0
    
    def bulk_token_operation(self, operation: str, amount: int, user_filter: Dict = None) -> int:
        """Perform bulk token operations on users"""
        conn = self.get_database_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            
            # Build query based on filter
            base_query = "SELECT id FROM users WHERE is_active = TRUE"
            params = []
            
            if user_filter:
                if 'min_tokens' in user_filter:
                    base_query += " AND tokens >= ?"
                    params.append(user_filter['min_tokens'])
                
                if 'max_tokens' in user_filter:
                    base_query += " AND tokens <= ?"
                    params.append(user_filter['max_tokens'])
                
                if 'min_redemptions' in user_filter:
                    base_query += " AND redemptions >= ?"
                    params.append(user_filter['min_redemptions'])
            
            cursor.execute(base_query, params)
            target_users = cursor.fetchall()
            
            affected_count = 0
            
            for user in target_users:
                user_id = user['id']
                
                if operation == 'add':
                    cursor.execute("UPDATE users SET tokens = tokens + ? WHERE id = ?", (amount, user_id))
                    cursor.execute("""
                        INSERT INTO token_transactions (user_id, amount, transaction_type, description) 
                        VALUES (?, ?, ?, ?)
                    """, (user_id, amount, "bulk_add", f"Bulk token addition by admin"))
                
                elif operation == 'subtract':
                    cursor.execute("UPDATE users SET tokens = MAX(0, tokens - ?) WHERE id = ?", (amount, user_id))
                    cursor.execute("""
                        INSERT INTO token_transactions (user_id, amount, transaction_type, description) 
                        VALUES (?, ?, ?, ?)
                    """, (user_id, -amount, "bulk_subtract", f"Bulk token subtraction by admin"))
                
                elif operation == 'set':
                    cursor.execute("UPDATE users SET tokens = ? WHERE id = ?", (amount, user_id))
                    cursor.execute("""
                        INSERT INTO token_transactions (user_id, amount, transaction_type, description) 
                        VALUES (?, ?, ?, ?)
                    """, (user_id, amount, "bulk_set", f"Bulk token set to {amount} by admin"))
                
                affected_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"Bulk operation '{operation}' applied to {affected_count} users")
            return affected_count
            
        except Exception as e:
            logger.error(f"Bulk operation error: {e}")
            conn.close()
            return 0
    
    def get_system_health(self) -> Dict:
        """Get system health metrics"""
        conn = self.get_database_connection()
        if not conn:
            return {'status': 'error', 'message': 'Database connection failed'}
        
        try:
            cursor = conn.cursor()
            
            # Database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size_mb = round((page_count * page_size) / (1024 * 1024), 2)
            
            # Table sizes
            tables = ['users', 'content', 'referrals', 'feedback', 'logs', 'token_transactions']
            table_sizes = {}
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                table_sizes[table] = cursor.fetchone()[0]
            
            # Recent error count
            cursor.execute("""
                SELECT COUNT(*) FROM logs 
                WHERE log_type = 'error' 
                AND timestamp >= datetime('now', '-24 hours')
            """)
            recent_errors = cursor.fetchone()[0]
            
            # System performance indicators
            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_activity) = DATE('now')")
            daily_active_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM token_transactions WHERE DATE(timestamp) = DATE('now')")
            daily_transactions = cursor.fetchone()[0]
            
            conn.close()
            
            # Determine system status
            status = 'healthy'
            warnings = []
            
            if db_size_mb > 100:  # Warning if DB > 100MB
                warnings.append(f"Large database size: {db_size_mb}MB")
            
            if recent_errors > 10:
                warnings.append(f"High error rate: {recent_errors} errors in 24h")
                status = 'warning'
            
            if table_sizes['logs'] > 10000:
                warnings.append("Log table needs cleanup")
            
            return {
                'status': status,
                'database_size_mb': db_size_mb,
                'table_sizes': table_sizes,
                'recent_errors': recent_errors,
                'daily_active_users': daily_active_users,
                'daily_transactions': daily_transactions,
                'warnings': warnings,
                'checked_at': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System health check error: {e}")
            conn.close()
            return {'status': 'error', 'message': str(e)}

# CLI interface for admin tools
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Telegram Bot Admin Tools')
    parser.add_argument('--export-users', action='store_true', help='Export user data to CSV')
    parser.add_argument('--export-content', action='store_true', help='Export content data to CSV')
    parser.add_argument('--generate-report', action='store_true', help='Generate comprehensive admin report')
    parser.add_argument('--system-health', action='store_true', help='Check system health')
    parser.add_argument('--cleanup-inactive', type=int, metavar='DAYS', help='Remove inactive users after N days')
    
    args = parser.parse_args()
    
    admin_tools = AdminToolkit()
    
    if args.export_users:
        file = admin_tools.export_user_data()
        print(f"User data exported to: {file}")
    
    if args.export_content:
        file = admin_tools.export_content_data()
        print(f"Content data exported to: {file}")
    
    if args.generate_report:
        file = admin_tools.generate_admin_report()
        print(f"Admin report generated: {file}")
    
    if args.system_health:
        health = admin_tools.get_system_health()
        print(json.dumps(health, indent=2))
    
    if args.cleanup_inactive:
        count = admin_tools.cleanup_inactive_users(args.cleanup_inactive)
        print(f"Cleaned up {count} inactive users")
