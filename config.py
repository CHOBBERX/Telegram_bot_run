"""
Production Configuration for Advanced Telegram Bot
Complete settings for token-based video system with enhanced features
"""

import os
from pathlib import Path

# ================================
# CORE BOT CONFIGURATION
# ================================

# Bot Authentication (Get from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot_username")  # Without @

# ================================
# ADMIN CONFIGURATION
# ================================

# Primary admin (numeric Telegram user ID)
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# Secondary admin (username without @)
ADDITIONAL_ADMIN = os.getenv("ADDITIONAL_ADMIN", "pb65walaa")

# Admin access levels
ADMIN_ROLES = {
    ADMIN_ID: "super_admin",  # Full access
    # Add more admins here: user_id: "admin"
}

# ================================
# CHANNEL CONFIGURATION
# ================================

# Channel for auto-posting content
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel_username")

# Channel posting settings
AUTO_POST_TO_CHANNEL = True
CHANNEL_POST_DELAY = 5  # seconds

# ================================
# PAYMENT CONFIGURATION
# ================================

# UPI Payment Details
UPI_ID = os.getenv("UPI_ID", "yourupi@upi")
PAYMENT_CURRENCY = "INR"

# Token pricing (in INR)
TOKEN_PACKAGES = {
    "starter": {"tokens": 5, "bonus": 0, "price": 50, "name": "Starter Pack"},
    "popular": {"tokens": 10, "bonus": 1, "price": 90, "name": "Popular Pack"},
    "premium": {"tokens": 25, "bonus": 3, "price": 200, "name": "Premium Pack"},
    "vip": {"tokens": 50, "bonus": 10, "price": 350, "name": "VIP Pack"}
}

# Payment verification
MANUAL_PAYMENT_VERIFICATION = True
AUTO_PAYMENT_VERIFICATION = False  # For future UPI API integration

# ================================
# TOKEN SYSTEM CONFIGURATION
# ================================

# Referral rewards
REFERRAL_BONUS = 2  # Tokens given per successful referral
MAX_REFERRAL_BONUS_PER_USER = 100  # Maximum referral earnings per user

# Loyalty system
LOYALTY_THRESHOLD = 10  # Redemptions needed for loyalty bonus
LOYALTY_BONUS = 5  # Bonus tokens for loyalty milestone

# Welcome bonus
WELCOME_BONUS = 1  # Free tokens for new users

# Token mechanics
TOKEN_TO_VIDEO_RATIO = 1  # 1 token = 1 video unlock
MIN_TOKENS_FOR_REDEMPTION = 1
MAX_TOKENS_PER_USER = 1000  # Anti-abuse measure

# ================================
# DATABASE CONFIGURATION
# ================================

# Database file location
DATABASE_FILE = os.getenv("DATABASE_FILE", "bot_database.db")

# Backup settings
AUTO_BACKUP = True
BACKUP_INTERVAL_HOURS = 24
BACKUP_RETENTION_DAYS = 30
BACKUP_DIRECTORY = "backups"

# Database optimization
AUTO_VACUUM = True
WAL_MODE = True  # Write-Ahead Logging for better performance

# ================================
# SECURITY CONFIGURATION
# ================================

# File upload restrictions
ALLOWED_FILE_TYPES = ['video', 'photo', 'document']
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
ALLOWED_VIDEO_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
ALLOWED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# Content moderation
ENABLE_CONTENT_MODERATION = True
AUTO_DELETE_INAPPROPRIATE_CONTENT = False
CONTENT_REVIEW_REQUIRED = False

# User security
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = 3600  # 1 hour in seconds

# ================================
# RATE LIMITING CONFIGURATION
# ================================

# Request rate limits
MAX_REQUESTS_PER_MINUTE = 30
MAX_REDEMPTIONS_PER_DAY = 50
MAX_REFERRALS_PER_DAY = 20

# Cooldown periods
COMMAND_COOLDOWN = 2  # seconds between commands
REDEMPTION_COOLDOWN = 5  # seconds between redemptions

# Anti-spam measures
MAX_IDENTICAL_MESSAGES = 3
SPAM_DETECTION_WINDOW = 60  # seconds

# ================================
# LOGGING CONFIGURATION
# ================================

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# Log rotation
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# What to log
LOG_USER_ACTIONS = True
LOG_ADMIN_ACTIONS = True
LOG_TRANSACTIONS = True
LOG_ERRORS = True
LOG_PERFORMANCE = False

# ================================
# FEATURE FLAGS
# ================================

# Core features
ENABLE_REFERRAL_SYSTEM = True
ENABLE_LOYALTY_PROGRAM = True
ENABLE_FEEDBACK_SYSTEM = True
ENABLE_LEADERBOARD = True

# Advanced features
ENABLE_CONTENT_CATEGORIES = True
ENABLE_USER_PROFILES = True
ENABLE_ANALYTICS = True
ENABLE_BROADCAST_SYSTEM = True

# Experimental features
ENABLE_AI_CONTENT_TAGS = False
ENABLE_SCHEDULED_POSTS = False
ENABLE_SUBSCRIPTION_TIERS = False

# ================================
# PERFORMANCE CONFIGURATION
# ================================

# Caching
ENABLE_USER_CACHE = True
CACHE_TIMEOUT = 300  # 5 minutes
MAX_CACHE_SIZE = 1000

# Database connection pooling
DB_POOL_SIZE = 5
DB_POOL_TIMEOUT = 30

# Async settings
MAX_CONCURRENT_REQUESTS = 100
REQUEST_TIMEOUT = 30

# ================================
# NOTIFICATION CONFIGURATION
# ================================

# Admin notifications
NOTIFY_ADMIN_ON_NEW_USER = False
NOTIFY_ADMIN_ON_PURCHASE = True
NOTIFY_ADMIN_ON_ERROR = True
NOTIFY_ADMIN_ON_HIGH_ACTIVITY = True

# User notifications
WELCOME_MESSAGE_ENABLED = True
LOYALTY_BONUS_NOTIFICATION = True
REFERRAL_SUCCESS_NOTIFICATION = True

# ================================
# CONTENT MANAGEMENT
# ================================

# Content organization
DEFAULT_CATEGORY = "General"
ENABLE_CONTENT_PREVIEW = True
CONTENT_DESCRIPTION_MAX_LENGTH = 500

# Content discovery
ENABLE_SEARCH = False  # Future feature
ENABLE_RECOMMENDATIONS = False  # Future feature
TRENDING_CONTENT_DAYS = 7

# ================================
# ANALYTICS CONFIGURATION
# ================================

# Data collection
COLLECT_USER_ANALYTICS = True
COLLECT_CONTENT_ANALYTICS = True
COLLECT_FINANCIAL_ANALYTICS = True

# Reporting
GENERATE_DAILY_REPORTS = True
GENERATE_WEEKLY_REPORTS = True
GENERATE_MONTHLY_REPORTS = True

# Data retention
ANALYTICS_RETENTION_DAYS = 365
LOG_RETENTION_DAYS = 90
SESSION_RETENTION_DAYS = 30

# ================================
# API CONFIGURATION
# ================================

# External APIs (for future features)
ENABLE_EXTERNAL_APIS = False
API_RATE_LIMIT = 100  # requests per hour
API_TIMEOUT = 10  # seconds

# Webhook configuration
WEBHOOK_ENABLED = False
WEBHOOK_URL = ""
WEBHOOK_SECRET = ""

# ================================
# MAINTENANCE CONFIGURATION
# ================================

# Automated maintenance
AUTO_CLEANUP_ENABLED = True
CLEANUP_SCHEDULE = "daily"  # daily, weekly, monthly
CLEANUP_OLD_LOGS = True
CLEANUP_INACTIVE_SESSIONS = True

# Maintenance mode
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "🔧 Bot is under maintenance. Please try again later."

# System monitoring
MONITOR_SYSTEM_HEALTH = True
HEALTH_CHECK_INTERVAL = 300  # 5 minutes
ALERT_ON_HIGH_ERROR_RATE = True

# ================================
# LOCALIZATION CONFIGURATION
# ================================

# Language settings
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ["en"]  # Future: ["en", "hi", "es", "fr"]
TIMEZONE = "Asia/Kolkata"

# Currency formatting
CURRENCY_SYMBOL = "₹"
CURRENCY_FORMAT = "{symbol}{amount:,.2f}"

# ================================
# DEVELOPMENT CONFIGURATION
# ================================

# Debug settings
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
VERBOSE_LOGGING = DEBUG_MODE
ENABLE_PROFILING = False

# Testing
ENABLE_TEST_COMMANDS = DEBUG_MODE
TEST_USER_ID = 12345  # For testing purposes
MOCK_PAYMENTS = DEBUG_MODE

# ================================
# ENVIRONMENT VALIDATION
# ================================

def validate_config():
    """Validate critical configuration values"""
    errors = []
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        errors.append("BOT_TOKEN must be configured")
    
    if ADMIN_ID == 123456789:
        errors.append("ADMIN_ID must be configured with actual Telegram user ID")
    
    if UPI_ID == "yourupi@upi":
        errors.append("UPI_ID should be configured with actual UPI ID")
    
    if not Path(BACKUP_DIRECTORY).exists() and AUTO_BACKUP:
        Path(BACKUP_DIRECTORY).mkdir(exist_ok=True)
    
    return errors

# ================================
# CONFIGURATION SUMMARY
# ================================

def get_config_summary():
    """Get a summary of current configuration"""
    return {
        "bot_configured": BOT_TOKEN != "YOUR_BOT_TOKEN_HERE",
        "admin_configured": ADMIN_ID != 123456789,
        "payment_configured": UPI_ID != "yourupi@upi",
        "features_enabled": {
            "referrals": ENABLE_REFERRAL_SYSTEM,
            "loyalty": ENABLE_LOYALTY_PROGRAM,
            "feedback": ENABLE_FEEDBACK_SYSTEM,
            "analytics": ENABLE_ANALYTICS,
        },
        "security_level": "high" if MAX_FILE_SIZE <= 50*1024*1024 else "medium",
        "database_file": DATABASE_FILE,
        "log_level": LOG_LEVEL
    }

# Validate configuration on import
if __name__ != "__main__":
    config_errors = validate_config()
    if config_errors:
        import logging
        logger = logging.getLogger(__name__)
        for error in config_errors:
            logger.warning(f"Configuration warning: {error}")
