#!/usr/bin/env python3
"""
Production-Ready Telegram Bot with Token-Based Video System
Features: Token economy, User management, Admin panel, Referral system, Analytics
Author: AI Assistant | Version: 2.0.0
"""

import logging
import sqlite3
import datetime
import asyncio
import os
import hashlib
import json
import re
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import quote

# Telegram Bot API imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

# Import configuration
from config import *
from database_setup import DatabaseManager

# Conversation states
WAITING_BROADCAST = 1
WAITING_TOKEN_AMOUNT = 2
WAITING_USER_ID = 3

# Enhanced logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting for bot actions"""
    def __init__(self):
        self.user_requests = {}
        self.user_redemptions = {}
    
    def check_rate_limit(self, user_id: int, action: str = 'request') -> bool:
        now = datetime.datetime.now()
        
        if action == 'request':
            if user_id not in self.user_requests:
                self.user_requests[user_id] = []
            
            # Clean old requests
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if (now - req_time).seconds < 60
            ]
            
            if len(self.user_requests[user_id]) >= MAX_REQUESTS_PER_MINUTE:
                return False
            
            self.user_requests[user_id].append(now)
            return True
        
        elif action == 'redemption':
            today = now.date()
            if user_id not in self.user_redemptions:
                self.user_redemptions[user_id] = {}
            
            if today not in self.user_redemptions[user_id]:
                self.user_redemptions[user_id][today] = 0
            
            if self.user_redemptions[user_id][today] >= MAX_REDEMPTIONS_PER_DAY:
                return False
            
            self.user_redemptions[user_id][today] += 1
            return True
        
        return True

class TelegramBotAdvanced:
    """Advanced Telegram Bot with comprehensive features"""
    
    def __init__(self):
        self.db = DatabaseManager(DATABASE_FILE)
        self.rate_limiter = RateLimiter()
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.bot_username = BOT_USERNAME
        self.setup_handlers()
        
        # Cache for frequently accessed data
        self.user_cache = {}
        self.content_cache = {}
        
        logger.info("🚀 Advanced Telegram Bot initialized successfully")
    
    def is_admin(self, user_id: int, username: str = None) -> bool:
        """Enhanced admin check"""
        if user_id == ADMIN_ID:
            return True
        
        if username:
            # Check both current and legacy admin usernames
            admin_usernames = [ADDITIONAL_ADMIN.lower().replace('@', '')]
            if username.lower().replace('@', '') in admin_usernames:
                return True
        
        return False
    
    def get_admin_level(self, user_id: int, username: str = None) -> str:
        """Get admin access level"""
        if user_id == ADMIN_ID:
            return "super_admin"
        elif self.is_admin(user_id, username):
            return "admin"
        return "user"
    
    def generate_referral_link(self, user_id: int) -> str:
        """Generate secure referral link"""
        return f"https://t.me/{self.bot_username}?start=ref_{user_id}"
    
    def format_currency(self, amount: float, currency: str = "INR") -> str:
        """Format currency display"""
        if currency == "INR":
            return f"₹{amount:,.2f}"
        return f"{amount:,.2f} {currency}"
    
    def create_progress_bar(self, current: int, total: int, width: int = 10) -> str:
        """Create ASCII progress bar"""
        filled = int((current / total) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar} {current}/{total}"
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("mytokens", self.mytokens_command))
        self.application.add_handler(CommandHandler("redeem", self.redeem_command))
        self.application.add_handler(CommandHandler("buy", self.buy_command))
        self.application.add_handler(CommandHandler("refer", self.refer_command))
        self.application.add_handler(CommandHandler("feedback", self.feedback_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        self.application.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("logs", self.logs_command))
        self.application.add_handler(CommandHandler("backup", self.backup_command))
        self.application.add_handler(CommandHandler("claimtokens", self.claimtokens_command))
        self.application.add_handler(CommandHandler("referrals", self.referrals_command))
        self.application.add_handler(CommandHandler("broadcast", self.broadcast_command))
        self.application.add_handler(CommandHandler("maintenance", self.maintenance_command))
        self.application.add_handler(CommandHandler("export", self.export_command))
        
        # Conversation handlers
        broadcast_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_broadcast, pattern="admin_broadcast")],
            states={
                WAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_broadcast)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)]
        )
        self.application.add_handler(broadcast_conv)
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handlers
        self.application.add_handler(
            MessageHandler(
                filters.PHOTO | filters.VIDEO | filters.DOCUMENT, 
                self.handle_media
            )
        )
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self.handle_text
            )
        )
        
        logger.info("✅ All handlers registered successfully")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced /start command with beautiful welcome"""
        user = update.effective_user
        args = context.args
        
        # Rate limiting
        if not self.rate_limiter.check_rate_limit(user.id):
            await update.message.reply_text("⚠️ Too many requests. Please wait a moment.")
            return
        
        # Process referral
        referral_by = None
        referral_bonus_msg = ""
        
        if args and args[0].startswith('ref_'):
            try:
                referral_by = int(args[0].split('_')[1])
                if referral_by == user.id:
                    referral_by = None  # Can't refer yourself
            except (ValueError, IndexError):
                pass
        
        # Get or create user
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT * FROM users WHERE id = ?", (user.id,))
            existing_user = cursor.fetchone()
            
            if not existing_user:
                # Create new user
                cursor.execute("""
                    INSERT INTO users (id, username, first_name, last_name, referral_by) 
                    VALUES (?, ?, ?, ?, ?)
                """, (user.id, user.username, user.first_name, user.last_name, referral_by))
                
                # Process referral bonus
                if referral_by:
                    cursor.execute("""
                        INSERT INTO referrals (referrer_id, referred_id, bonus_amount) 
                        VALUES (?, ?, ?)
                    """, (referral_by, user.id, REFERRAL_BONUS))
                    
                    cursor.execute("""
                        UPDATE users SET tokens = tokens + ? WHERE id = ?
                    """, (REFERRAL_BONUS, referral_by))
                    
                    cursor.execute("""
                        INSERT INTO token_transactions 
                        (user_id, amount, transaction_type, description) 
                        VALUES (?, ?, ?, ?)
                    """, (referral_by, REFERRAL_BONUS, "referral_bonus", f"Referred user @{user.username or user.first_name}"))
                    
                    referral_bonus_msg = f"\n\n🎉 Welcome bonus! Your referrer earned {REFERRAL_BONUS} tokens!"
                    
                    # Log referral
                    cursor.execute("""
                        INSERT INTO logs (log_type, message, user_id) 
                        VALUES (?, ?, ?)
                    """, ("referral", f"User {user.id} referred by {referral_by}", user.id))
                
                # Welcome bonus for new users
                cursor.execute("""
                    UPDATE users SET tokens = tokens + 1 WHERE id = ?
                """, (user.id,))
                
                cursor.execute("""
                    INSERT INTO token_transactions 
                    (user_id, amount, transaction_type, description) 
                    VALUES (?, ?, ?, ?)
                """, (user.id, 1, "welcome_bonus", "Welcome to the platform"))
                
                user_status = "new"
            else:
                user_status = "returning"
                # Update last activity
                cursor.execute("""
                    UPDATE users SET last_activity = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (user.id,))
            
            # Get current user data
            cursor.execute("SELECT tokens, redemptions FROM users WHERE id = ?", (user.id,))
            user_data = cursor.fetchone()
            tokens, redemptions = user_data if user_data else (0, 0)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database error in start_command: {e}")
            await update.message.reply_text("❌ Database error. Please try again later.")
            return
        
        # Create welcome message
        if user_status == "new":
            welcome_text = f"""
🎬 **Welcome to Premium Content Hub!** 🎬

Hello {user.first_name}! 👋

🎯 **You're all set up!**
• 💰 Starting balance: **{tokens} tokens**
• 🎁 1 FREE token as welcome bonus!
• 🔓 Each token unlocks 1 premium video

🌟 **How it works:**
• Browse exclusive content library
• Use tokens to unlock videos instantly
• Earn more through referrals & purchases
• Enjoy premium quality content

📈 **Earning Opportunities:**
• 🤝 Refer friends: **+{REFERRAL_BONUS} tokens each**
• 💳 Purchase packages with great discounts
• 🏆 Loyalty rewards every {LOYALTY_THRESHOLD} redemptions

{referral_bonus_msg}
"""
        else:
            welcome_text = f"""
🎬 **Welcome back to Premium Content Hub!** 🎬

Great to see you again, {user.first_name}! 👋

💰 **Your Status:**
• Current balance: **{tokens} tokens**
• Total redemptions: **{redemptions}**
• Loyalty progress: {redemptions % LOYALTY_THRESHOLD}/{LOYALTY_THRESHOLD}

🚀 **Ready to continue your journey?**
"""
        
        # Create interactive keyboard
        keyboard = [
            [
                InlineKeyboardButton("🎬 Browse Content", callback_data="browse_content"),
                InlineKeyboardButton("💰 My Tokens", callback_data="check_balance")
            ],
            [
                InlineKeyboardButton("🛒 Buy Tokens", callback_data="buy_tokens"),
                InlineKeyboardButton("🤝 Refer Friends", callback_data="refer_friends")
            ],
            [
                InlineKeyboardButton("👤 My Profile", callback_data="user_profile"),
                InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
            ],
            [
                InlineKeyboardButton("💬 Feedback", callback_data="feedback"),
                InlineKeyboardButton("ℹ️ Help", callback_data="help")
            ]
        ]
        
        # Add admin button for administrators
        if self.is_admin(user.id, user.username):
            keyboard.append([InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Log user activity
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (log_type, message, user_id) 
                VALUES (?, ?, ?)
            """, ("user_activity", f"User started bot - Status: {user_status}", user.id))
            conn.commit()
            conn.close()
        except:
            pass
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comprehensive help command"""
        help_text = """
📚 **Premium Content Hub - Help Guide** 📚

🎯 **Getting Started:**
• Use /start to begin your journey
• Receive 1 FREE welcome token
• Browse our premium content library

💰 **Token System:**
• 1 token = 1 video unlock
• Tokens never expire
• Secure payment via UPI

🔧 **Available Commands:**

**👤 User Commands:**
/mytokens - Check your token balance
/redeem - Browse and unlock content
/buy - Purchase token packages
/refer - Get your referral link
/profile - View your complete profile
/feedback - Rate our service
/leaderboard - See top users

**🎁 Earning Tokens:**
• 🤝 Referrals: {REFERRAL_BONUS} tokens per friend
• 💳 Purchase packages (bulk discounts!)
• 🏆 Loyalty bonus: {LOYALTY_BONUS} tokens every {LOYALTY_THRESHOLD} redemptions

**💡 Pro Tips:**
• Share your referral link on social media
• Purchase larger packages for better value
• Check leaderboard for inspiration
• Leave feedback to help us improve

**🔒 Security & Privacy:**
• Your data is fully encrypted
• Secure UPI payment processing
• No personal info shared with third parties

**❓ Need More Help?**
Contact our admin team or use /feedback for specific questions!
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🎬 Start Browsing", callback_data="browse_content"),
                InlineKeyboardButton("🤝 Refer Now", callback_data="refer_friends")
            ],
            [
                InlineKeyboardButton("🛒 Buy Tokens", callback_data="buy_tokens"),
                InlineKeyboardButton("📊 My Profile", callback_data="user_profile")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def mytokens_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced token balance display"""
        user = update.effective_user
        
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Get comprehensive user data
            cursor.execute("""
                SELECT tokens, redemptions, joined_on, total_spent, loyalty_points 
                FROM users WHERE id = ?
            """, (user.id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                conn.close()
                await update.message.reply_text("❌ Please use /start first to register!")
                return
            
            tokens, redemptions, joined_on, total_spent, loyalty_points = user_data
            
            # Get recent transactions
            cursor.execute("""
                SELECT transaction_type, amount, description, timestamp 
                FROM token_transactions 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 5
            """, (user.id,))
            recent_transactions = cursor.fetchall()
            
            # Get referral count
            cursor.execute("""
                SELECT COUNT(*) FROM referrals WHERE referrer_id = ?
            """, (user.id,))
            referral_count = cursor.fetchone()[0]
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Database error in mytokens_command: {e}")
            await update.message.reply_text("❌ Database error. Please try again.")
            return
        
        # Calculate loyalty progress
        loyalty_progress = redemptions % LOYALTY_THRESHOLD
        progress_bar = self.create_progress_bar(loyalty_progress, LOYALTY_THRESHOLD)
        
        # Format join date
        join_date = datetime.datetime.strptime(joined_on, "%Y-%m-%d %H:%M:%S").strftime("%B %d, %Y")
        
        # Create detailed balance report
        balance_text = f"""
💎 **Your Token Wallet** 💎

💰 **Current Balance:** `{tokens} tokens`
🎬 **Total Unlocked:** `{redemptions} videos`
👥 **Friends Referred:** `{referral_count}`
💸 **Total Spent:** `{self.format_currency(total_spent or 0)}`

📅 **Member Since:** {join_date}

🏆 **Loyalty Progress:**
{progress_bar}
`{LOYALTY_THRESHOLD - loyalty_progress} more unlocks for {LOYALTY_BONUS} bonus tokens!`

💡 **Token Value:**
• Each token = 1 premium video
• Average video value: ₹10-20
• Your wallet value: `{self.format_currency(tokens * 15)}`

📈 **Recent Activity:**
"""
        
        # Add recent transactions
        if recent_transactions:
            for transaction in recent_transactions:
                trans_type, amount, description, timestamp = transaction
                date = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%m/%d")
                
                if amount > 0:
                    emoji = "💚"
                    sign = "+"
                else:
                    emoji = "❤️"
                    sign = ""
                
                balance_text += f"• {emoji} {sign}{amount} - {description} ({date})\n"
        else:
            balance_text += "• No recent transactions\n"
        
        balance_text += f"""

🎯 **Quick Actions:**
"""
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("🎬 Redeem Tokens", callback_data="redeem_tokens"),
                InlineKeyboardButton("🛒 Buy More", callback_data="buy_tokens")
            ],
            [
                InlineKeyboardButton("🤝 Earn More", callback_data="refer_friends"),
                InlineKeyboardButton("📊 Full Profile", callback_data="user_profile")
            ],
            [
                InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
                InlineKeyboardButton("📈 Statistics", callback_data="user_stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            balance_text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def redeem_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced content redemption with categories"""
        user = update.effective_user
        
        # Check rate limit
        if not self.rate_limiter.check_rate_limit(user.id, 'redemption'):
            await update.message.reply_text(
                "⚠️ Daily redemption limit reached. Try again tomorrow!"
            )
            return
        
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Get user data
            cursor.execute("SELECT tokens FROM users WHERE id = ?", (user.id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                conn.close()
                await update.message.reply_text("❌ Please use /start first!")
                return
            
            tokens = user_data[0]
            
            if tokens <= 0:
                conn.close()
                no_tokens_msg = """
😔 **Insufficient Tokens** 😔

You need tokens to unlock premium content!

🎁 **Ways to Get Tokens:**
• 🤝 Refer friends (+{} tokens each)
• 💳 Purchase packages (best value!)
• 🏆 Loyalty rewards every {} redemptions

💡 **Special Offer:** Get 10 tokens for just ₹90 (₹10 discount!)
""".format(REFERRAL_BONUS, LOYALTY_THRESHOLD)
                
                keyboard = [
                    [
                        InlineKeyboardButton("🛒 Buy Tokens", callback_data="buy_tokens"),
                        InlineKeyboardButton("🤝 Refer Friends", callback_data="refer_friends")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    no_tokens_msg, 
                    reply_markup=reply_markup, 
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Get available content with categories
            cursor.execute("""
                SELECT id, file_id, file_type, caption, category, views, uploaded_on 
                FROM content 
                WHERE is_active = TRUE 
                ORDER BY uploaded_on DESC 
                LIMIT 20
            """)
            content_list = cursor.fetchall()
            
            conn.close()
            
            if not content_list:
                await update.message.reply_text(
                    "📭 No content available at the moment. Check back later!"
                )
                return
            
        except Exception as e:
            logger.error(f"Database error in redeem_command: {e}")
            await update.message.reply_text("❌ Database error. Please try again.")
            return
        
        # Create content selection interface
        selection_text = f"""
🎬 **Premium Content Library** 🎬

💰 **Your Balance:** {tokens} tokens
🎯 **Unlock Cost:** 1 token per video

📚 **Available Content ({len(content_list)} videos):**
"""
        
        # Group content by category
        categories = {}
        for content in content_list:
            category = content[4] or "General"
            if category not in categories:
                categories[category] = []
            categories[category].append(content)
        
        # Create category buttons
        keyboard = []
        for category, items in categories.items():
            emoji = {"General": "🎬", "Premium": "⭐", "Latest": "🆕", "Popular": "🔥"}.get(category, "📁")
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {category} ({len(items)})", 
                    callback_data=f"category_{category}"
                )
            ])
        
        # Add individual content buttons (first 8 items)
        keyboard.append([InlineKeyboardButton("➡️ Browse All Content", callback_data="browse_all")])
        
        for i, content in enumerate(content_list[:6]):  # Show first 6 items
            content_id, file_id, file_type, caption, category, views, uploaded_on = content
            
            # Truncate caption
            short_caption = caption[:35] + "..." if len(caption) > 35 else caption
            
            keyboard.append([
                InlineKeyboardButton(
                    f"🎬 {short_caption} ({views} views)", 
                    callback_data=f"unlock_{content_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu"),
            InlineKeyboardButton("💰 Buy Tokens", callback_data="buy_tokens")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            selection_text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def buy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced purchase interface with packages"""
        purchase_text = f"""
💰 **Token Purchase Center** 💰

🏦 **Payment Method:** UPI (Instant)
📱 **UPI ID:** `{UPI_ID}`

💎 **Available Packages:**

🥉 **Starter Pack - ₹50**
• 5 tokens
• Perfect for trying our service
• ₹10 per token

🥈 **Popular Pack - ₹90** ⭐
• 10 tokens + 1 bonus
• Save ₹10 (Best Value!)
• ₹8.18 per token

🥇 **Premium Pack - ₹200**
• 25 tokens + 3 bonus
• Save ₹50 (Great Deal!)
• ₹7.14 per token

💎 **VIP Pack - ₹350**
• 50 tokens + 10 bonus
• Save ₹150 (Maximum Savings!)
• ₹5.83 per token

📋 **How to Purchase:**
1️⃣ Choose your package below
2️⃣ Send payment to UPI ID above
3️⃣ Take screenshot of payment confirmation
4️⃣ Forward screenshot to admin
5️⃣ Tokens credited within 5 minutes!

⚡ **Fast Track:** Send payment proof directly to admin for instant processing!

🔒 **100% Secure:** All transactions are encrypted and verified.
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🥉 Starter (₹50)", callback_data="package_starter"),
                InlineKeyboardButton("🥈 Popular (₹90)", callback_data="package_popular")
            ],
            [
                InlineKeyboardButton("🥇 Premium (₹200)", callback_data="package_premium"),
                InlineKeyboardButton("💎 VIP (₹350)", callback_data="package_vip")
            ],
            [
                InlineKeyboardButton("📋 Copy UPI ID", callback_data=f"copy_upi"),
                InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADDITIONAL_ADMIN}")
            ],
            [
                InlineKeyboardButton("💡 Payment Guide", callback_data="payment_guide"),
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            purchase_text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def refer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced referral system with tracking"""
        user = update.effective_user
        referral_link = self.generate_referral_link(user.id)
        
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Get referral statistics
            cursor.execute("""
                SELECT COUNT(*) as total_referrals,
                       SUM(bonus_amount) as total_earned
                FROM referrals 
                WHERE referrer_id = ?
            """, (user.id,))
            stats = cursor.fetchone()
            total_referrals, total_earned = stats if stats else (0, 0)
            
            # Get recent referrals
            cursor.execute("""
                SELECT u.first_name, u.username, r.referred_on, r.bonus_amount
                FROM referrals r
                JOIN users u ON r.referred_id = u.id
                WHERE r.referrer_id = ?
                ORDER BY r.referred_on DESC
                LIMIT 5
            """, (user.id,))
            recent_referrals = cursor.fetchall()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Database error in refer_command: {e}")
            total_referrals, total_earned = 0, 0
            recent_referrals = []
        
        referral_text = f"""
🤝 **Referral Program** 🤝

🔗 **Your Personal Link:**
`{referral_link}`

📊 **Your Referral Stats:**
• 👥 Total Referrals: **{total_referrals}**
• 💰 Tokens Earned: **{total_earned or 0}**
• 🎁 Per Referral: **{REFERRAL_BONUS} tokens**

🎯 **How It Works:**
1️⃣ Share your unique link
2️⃣ Friends join and use /start
3️⃣ You earn {REFERRAL_BONUS} tokens instantly
4️⃣ No limit on referrals!

🚀 **Boost Your Earnings:**
• Share in WhatsApp groups
• Post on social media
• Tell friends about premium content
• Create engaging posts with your link

💡 **Pro Tips:**
• Mention the free welcome token
• Highlight exclusive content
• Share success stories
• Be genuine and helpful
"""
        
        if recent_referrals:
            referral_text += "\n🏆 **Recent Referrals:**\n"
            for referral in recent_referrals:
                name = referral[1] if referral[1] else referral[0]
                date = datetime.datetime.strptime(referral[2], "%Y-%m-%d %H:%M:%S").strftime("%m/%d")
                referral_text += f"• @{name} ({date}) - +{referral[3]} tokens\n"
        
        # Create sharing buttons
        keyboard = [
            [
                InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_referral"),
                InlineKeyboardButton("📊 My Stats", callback_data="referral_stats")
            ],
            [
                InlineKeyboardButton("💬 Share on WhatsApp", 
                                   url=f"https://wa.me/?text=🎬 Join me on Premium Content Hub! Get FREE tokens and unlock exclusive videos! {quote(referral_link)}"),
                InlineKeyboardButton("📤 Share on Telegram", 
                                   url=f"https://t.me/share/url?url={quote(referral_link)}&text=🎬 Amazing premium content platform! Join now!")
            ],
            [
                InlineKeyboardButton("🏆 Top Referrers", callback_data="top_referrers"),
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            referral_text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comprehensive admin panel"""
        user = update.effective_user
        
        if not self.is_admin(user.id, user.username):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return
        
        admin_level = self.get_admin_level(user.id, user.username)
        
        try:
            # Get quick stats for admin dashboard
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM content WHERE is_active = TRUE")
            total_content = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM token_transactions WHERE DATE(timestamp) = DATE('now')")
            today_transactions = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(tokens) FROM users")
            total_tokens_in_system = cursor.fetchone()[0] or 0
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Admin stats error: {e}")
            total_users = total_content = today_transactions = total_tokens_in_system = 0
        
        admin_text = f"""
🛠️ **Admin Control Panel** 🛠️

👤 **Access Level:** {admin_level.title()}
📊 **Quick Stats:**
• 👥 Total Users: {total_users}
• 🎬 Active Content: {total_content}
• 💰 Tokens in System: {total_tokens_in_system}
• 📈 Today's Transactions: {today_transactions}

⚡ **Quick Actions:**
"""
        
        # Create admin keyboard based on access level
        keyboard = [
            [
                InlineKeyboardButton("📤 Upload Content", callback_data="admin_upload"),
                InlineKeyboardButton("🗂️ Manage Content", callback_data="admin_content")
            ],
            [
                InlineKeyboardButton("👥 User Management", callback_data="admin_users"),
                InlineKeyboardButton("🎁 Token Manager", callback_data="admin_tokens")
            ],
            [
                InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton("💰 Payments", callback_data="admin_payments"),
                InlineKeyboardButton("🔧 Settings", callback_data="admin_settings")
            ]
        ]
        
        # Super admin only features
        if admin_level == "super_admin":
            keyboard.extend([
                [
                    InlineKeyboardButton("🗄️ Database", callback_data="admin_database"),
                    InlineKeyboardButton("📝 Logs", callback_data="admin_logs")
                ],
                [
                    InlineKeyboardButton("⚙️ Maintenance", callback_data="admin_maintenance"),
                    InlineKeyboardButton("📦 Export Data", callback_data="admin_export")
                ]
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Exit Admin", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            admin_text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced callback handler with comprehensive actions"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = query.from_user
        
        try:
            # Main menu callbacks
            if data == "main_menu":
                await self.start_command(update, context)
            
            elif data == "browse_content":
                await self.redeem_command(update, context)
            
            elif data == "check_balance":
                await self.mytokens_command(update, context)
            
            elif data == "buy_tokens":
                await self.buy_command(update, context)
            
            elif data == "refer_friends":
                await self.refer_command(update, context)
            
            elif data == "help":
                await self.help_command(update, context)
            
            # Content unlocking
            elif data.startswith("unlock_"):
                await self.handle_unlock(query, context, data)
            
            # Package selection
            elif data.startswith("package_"):
                await self.handle_package_selection(query, context, data)
            
            # Copy actions
            elif data == "copy_upi":
                await query.edit_message_text(
                    f"📋 **UPI ID Copied!**\n\n`{UPI_ID}`\n\nPaste this in your payment app.",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif data == "copy_referral":
                link = self.generate_referral_link(user.id)
                await query.edit_message_text(
                    f"📋 **Referral Link Copied!**\n\n`{link}`\n\nShare this link to earn tokens!",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            # Admin callbacks
            elif data.startswith("admin_"):
                await self.handle_admin_callback(query, context, data)
            
            # User profile and stats
            elif data == "user_profile":
                await self.show_user_profile(query, context)
            
            elif data == "leaderboard":
                await self.show_leaderboard(query, context)
            
            # Feedback system
            elif data == "feedback":
                await self.show_feedback_options(query, context)
            
            elif data.startswith("rate_"):
                await self.handle_rating(query, context, data)
            
            # Cancel action
            elif data == "cancel":
                await query.edit_message_text("❌ Operation cancelled.")
            
            else:
                await query.edit_message_text("❓ Unknown action. Please try again.")
                
        except Exception as e:
            logger.error(f"Callback handler error: {e}")
            await query.edit_message_text("❌ An error occurred. Please try again.")
    
    async def handle_unlock(self, query, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle content unlock with enhanced experience"""
        user = query.from_user
        content_id = int(data.split('_')[1])
        
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Get user data
            cursor.execute("SELECT tokens, redemptions FROM users WHERE id = ?", (user.id,))
            user_data = cursor.fetchone()
            
            if not user_data or user_data[0] <= 0:
                conn.close()
                await query.edit_message_text("❌ Insufficient tokens! Use /buy to purchase more.")
                return
            
            tokens, redemptions = user_data
            
            # Get content details
            cursor.execute("""
                SELECT file_id, file_type, caption, views, category 
                FROM content 
                WHERE id = ? AND is_active = TRUE
            """, (content_id,))
            content = cursor.fetchone()
            
            if not content:
                conn.close()
                await query.edit_message_text("❌ Content not found or no longer available.")
                return
            
            file_id, file_type, caption, views, category = content
            
            # Process unlock transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Deduct token
            cursor.execute("UPDATE users SET tokens = tokens - 1, redemptions = redemptions + 1 WHERE id = ?", (user.id,))
            
            # Update content views
            cursor.execute("UPDATE content SET views = views + 1 WHERE id = ?", (content_id,))
            
            # Log transaction
            cursor.execute("""
                INSERT INTO token_transactions (user_id, amount, transaction_type, description, content_id) 
                VALUES (?, ?, ?, ?, ?)
            """, (user.id, -1, "redeem", f"Unlocked: {caption[:50]}", content_id))
            
            # Check for loyalty bonus
            new_redemptions = redemptions + 1
            loyalty_bonus_msg = ""
            
            if new_redemptions % LOYALTY_THRESHOLD == 0:
                cursor.execute("UPDATE users SET tokens = tokens + ? WHERE id = ?", (LOYALTY_BONUS, user.id))
                cursor.execute("""
                    INSERT INTO token_transactions (user_id, amount, transaction_type, description) 
                    VALUES (?, ?, ?, ?)
                """, (user.id, LOYALTY_BONUS, "loyalty_bonus", f"Milestone reward for {new_redemptions} redemptions"))
                loyalty_bonus_msg = f"\n\n🎉 **LOYALTY BONUS!** 🎉\nYou earned {LOYALTY_BONUS} tokens for reaching {new_redemptions} redemptions!"
            
            cursor.execute("COMMIT")
            
            # Get updated balance
            cursor.execute("SELECT tokens FROM users WHERE id = ?", (user.id,))
            updated_tokens = cursor.fetchone()[0]
            
            conn.close()
            
            # Send the content
            success_msg = f"""
✅ **Content Unlocked Successfully!** ✅

🎬 **{caption}**
📁 Category: {category or 'General'}
👁️ Views: {views + 1}

💰 Remaining Balance: **{updated_tokens} tokens**
🎯 Total Unlocked: **{new_redemptions} videos**

{loyalty_bonus_msg}

📱 **Content delivered below:**
"""
            
            try:
                if file_type == 'video':
                    await context.bot.send_video(
                        user.id,
                        file_id,
                        caption=success_msg,
                        parse_mode=ParseMode.MARKDOWN
                    )
                elif file_type == 'photo':
                    await context.bot.send_photo(
                        user.id,
                        file_id,
                        caption=success_msg,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await context.bot.send_document(
                        user.id,
                        file_id,
                        caption=success_msg,
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                # Success message in group/channel
                await query.edit_message_text(
                    "✅ Content unlocked and sent to your private messages! 📱",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Log successful unlock
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO logs (log_type, message, user_id, content_id) 
                    VALUES (?, ?, ?, ?)
                """, ("content_unlock", f"Successfully unlocked content {content_id}", user.id, content_id))
                conn.commit()
                conn.close()
                
            except Exception as send_error:
                # Refund token if sending fails
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET tokens = tokens + 1, redemptions = redemptions - 1 WHERE id = ?", (user.id,))
                cursor.execute("""
                    INSERT INTO token_transactions (user_id, amount, transaction_type, description) 
                    VALUES (?, ?, ?, ?)
                """, (user.id, 1, "refund", f"Failed to send content {content_id}"))
                conn.commit()
                conn.close()
                
                await query.edit_message_text("❌ Failed to send content. Token refunded to your account.")
                logger.error(f"Failed to send content to user {user.id}: {send_error}")
        
        except Exception as e:
            logger.error(f"Unlock error: {e}")
            await query.edit_message_text("❌ Transaction failed. Please try again.")
    
    async def handle_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced media upload handler for admins"""
        user = update.effective_user
        
        if not self.is_admin(user.id, user.username):
            return
        
        message = update.message
        file_info = None
        file_type = None
        file_size = 0
        
        # Determine file type and get info
        if message.video:
            file_info = message.video
            file_type = 'video'
            file_size = file_info.file_size
        elif message.photo:
            file_info = message.photo[-1]
            file_type = 'photo'
            file_size = file_info.file_size
        elif message.document:
            file_info = message.document
            file_type = 'document'
            file_size = file_info.file_size
        
        if not file_info:
            return
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            await message.reply_text(f"❌ File too large. Maximum size: {MAX_FILE_SIZE/1024/1024:.0f}MB")
            return
        
        # Validate file type
        if file_type not in ALLOWED_FILE_TYPES:
            await message.reply_text(f"❌ File type not allowed. Allowed: {', '.join(ALLOWED_FILE_TYPES)}")
            return
        
        try:
            file_id = file_info.file_id
            caption = message.caption or "No caption provided"
            
            # Enhanced content metadata
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO content (file_id, file_type, caption, uploaded_by, file_size, category) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (file_id, file_type, caption, user.id, file_size, "General"))
            
            content_id = cursor.lastrowid
            
            # Log admin action
            cursor.execute("""
                INSERT INTO admin_actions (admin_id, action_type, details) 
                VALUES (?, ?, ?)
            """, (user.id, "content_upload", f"Uploaded {file_type}: {caption[:50]}"))
            
            conn.commit()
            conn.close()
            
            # Auto-post to channel if configured
            channel_posted = False
            if CHANNEL_ID and CHANNEL_ID.startswith('@'):
                try:
                    channel_caption = f"🎬 **New Content Available!**\n\n{caption}\n\n🤖 Use our bot to unlock premium content!"
                    
                    if file_type == 'video':
                        await context.bot.send_video(CHANNEL_ID, file_id, caption=channel_caption, parse_mode=ParseMode.MARKDOWN)
                    elif file_type == 'photo':
                        await context.bot.send_photo(CHANNEL_ID, file_id, caption=channel_caption, parse_mode=ParseMode.MARKDOWN)
                    else:
                        await context.bot.send_document(CHANNEL_ID, file_id, caption=channel_caption, parse_mode=ParseMode.MARKDOWN)
                    
                    channel_posted = True
                    
                except Exception as channel_error:
                    logger.error(f"Failed to post to channel: {channel_error}")
            
            # Success response
            success_text = f"""
✅ **Content Uploaded Successfully!**

🆔 **Content ID:** {content_id}
📝 **Caption:** {caption}
📁 **Type:** {file_type.title()}
📏 **Size:** {file_size/1024:.1f} KB
📺 **Channel Posted:** {'✅ Yes' if channel_posted else '❌ Failed'}

🎯 **Quick Actions:**
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("🗂️ View All Content", callback_data="admin_content"),
                    InlineKeyboardButton("📤 Upload More", callback_data="admin_upload")
                ],
                [
                    InlineKeyboardButton("📊 Content Stats", callback_data="content_stats"),
                    InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_panel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                success_text, 
                reply_markup=reply_markup, 
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Media upload error: {e}")
            await message.reply_text("❌ Upload failed. Please try again.")
    
    def run(self):
        """Start the bot with enhanced error handling"""
        logger.info("🚀 Starting Advanced Telegram Bot...")
        
        # Add error handler
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Update {update} caused error {context.error}")
            
            # Log error to database
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO logs (log_type, message, user_id, severity) 
                    VALUES (?, ?, ?, ?)
                """, ("error", str(context.error), update.effective_user.id if update.effective_user else None, "ERROR"))
                conn.commit()
                conn.close()
            except:
                pass
        
        self.application.add_error_handler(error_handler)
        
        # Run the bot
        self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

def main():
    """Main function with enhanced startup"""
    try:
        # Validate configuration
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            logger.error("❌ Please configure BOT_TOKEN in config.py")
            return
        
        if ADMIN_ID == 123456789:
            logger.error("❌ Please configure ADMIN_ID in config.py")
            return
        
        # Initialize and run bot
        bot = TelegramBotAdvanced()
        logger.info("✅ Configuration validated successfully")
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}")

if __name__ == "__main__":
    main()
