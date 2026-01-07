import requests
from datetime import datetime
import json

class NotificationManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def send_discord_notification(self, webhook_url, signal_data, user_id):
        """
        Send FVG signal notification to Discord
        
        Parameters:
        - webhook_url: Discord webhook URL
        - signal_data: Dictionary containing signal information
        - user_id: User ID for personalization
        """
        try:
            # Get username
            username = self._get_username(user_id)
            
            # Determine embed color based on FVG type
            color = 3066993 if signal_data['fvg_type'] == 'Bullish' else 15158332  # Green or Red
            
            # Build the embed
            embed = {
                "title": "🎯 FVG Signal Detected",
                "description": f"Fair Value Gap signal triggered for **{signal_data['symbol']}**",
                "color": color,
                "fields": [
                    {
                        "name": "📊 Symbol",
                        "value": signal_data['symbol'],
                        "inline": True
                    },
                    {
                        "name": "⏰ Price Timeframe",
                        "value": signal_data.get('price_timeframe', 'N/A'),
                        "inline": True
                    },
                    {
                        "name": "📈 FVG Timeframe",
                        "value": signal_data.get('fvg_timeframe', 'N/A'),
                        "inline": True
                    },
                    {
                        "name": "💰 Price Level",
                        "value": f"${signal_data['price_level']:.2f}",
                        "inline": True
                    },
                    {
                        "name": "📈 FVG Type",
                        "value": signal_data['fvg_type'],
                        "inline": True
                    },
                    {
                        "name": "💵 Trigger Price",
                        "value": f"${signal_data['trigger_price']:.2f}",
                        "inline": True
                    },
                    {
                        "name": "👤 User",
                        "value": username,
                        "inline": True
                    },
                    {
                        "name": "📍 FVG Zone",
                        "value": f"Low: ${signal_data['fvg_low']:.2f}\nHigh: ${signal_data['fvg_high']:.2f}",
                        "inline": False
                    },
                    {
                        "name": "ℹ️ How Signal Triggered",
                        "value": f"Price tapped **${signal_data['price_level']:.2f}** on **{signal_data.get('price_timeframe', 'N/A')}** chart, then FVG formed on **{signal_data.get('fvg_timeframe', 'N/A')}** chart",
                        "inline": False
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "FVG Trading Platform"
                }
            }
            
            # Add trading suggestion based on FVG type
            if signal_data['fvg_type'] == 'Bullish':
                embed['fields'].append({
                    "name": "💡 Trading Suggestion",
                    "value": f"**Bullish FVG detected!**\n• Consider LONG positions\n• Entry: Near ${signal_data['fvg_low']:.2f}\n• Target: ${signal_data['fvg_high']:.2f}+\n• Watch for price action in FVG zone",
                    "inline": False
                })
            else:
                embed['fields'].append({
                    "name": "💡 Trading Suggestion",
                    "value": f"**Bearish FVG detected!**\n• Consider SHORT positions\n• Entry: Near ${signal_data['fvg_high']:.2f}\n• Target: ${signal_data['fvg_low']:.2f}-\n• Watch for price action in FVG zone",
                    "inline": False
                })
            
            # Prepare payload
            payload = {
                "embeds": [embed],
                "username": "FVG Trading Bot",
                "avatar_url": "https://i.imgur.com/AfFp7pu.png"
            }
            
            # Send to Discord
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                return True, "Notification sent successfully"
            else:
                return False, f"Discord API error: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error sending notification: {str(e)}"
    
    def send_test_notification(self, webhook_url, username):
        """
        Send a test notification to verify webhook
        """
        try:
            embed = {
                "title": "✅ Test Notification",
                "description": "Your Discord webhook is configured correctly!",
                "color": 5763719,  # Blue
                "fields": [
                    {
                        "name": "👤 User",
                        "value": username,
                        "inline": True
                    },
                    {
                        "name": "⏰ Time",
                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "FVG Trading Platform - Test Message"
                }
            }
            
            payload = {
                "embeds": [embed],
                "username": "FVG Trading Bot"
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return response.status_code in [200, 204]
            
        except Exception as e:
            print(f"Test notification failed: {str(e)}")
            return False
    
    def send_daily_summary(self, webhook_url, user_id, summary_data):
        """
        Send daily trading summary
        """
        try:
            username = self._get_username(user_id)
            
            embed = {
                "title": "📊 Daily Trading Summary",
                "description": f"Summary for {datetime.now().strftime('%Y-%m-%d')}",
                "color": 3447003,  # Blue
                "fields": [
                    {
                        "name": "👤 Trader",
                        "value": username,
                        "inline": False
                    },
                    {
                        "name": "🎯 Total Signals",
                        "value": str(summary_data.get('total_signals', 0)),
                        "inline": True
                    },
                    {
                        "name": "📈 Bullish Signals",
                        "value": str(summary_data.get('bullish_signals', 0)),
                        "inline": True
                    },
                    {
                        "name": "📉 Bearish Signals",
                        "value": str(summary_data.get('bearish_signals', 0)),
                        "inline": True
                    },
                    {
                        "name": "💰 Most Active Symbol",
                        "value": summary_data.get('most_active_symbol', 'N/A'),
                        "inline": True
                    },
                    {
                        "name": "⏰ Most Active Timeframe",
                        "value": summary_data.get('most_active_timeframe', 'N/A'),
                        "inline": True
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "FVG Trading Platform - Daily Summary"
                }
            }
            
            payload = {
                "embeds": [embed],
                "username": "FVG Trading Bot"
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return response.status_code in [200, 204]
            
        except Exception as e:
            print(f"Daily summary notification failed: {str(e)}")
            return False
    
    def send_price_alert(self, webhook_url, user_id, alert_data):
        """
        Send price alert notification
        """
        try:
            username = self._get_username(user_id)
            
            embed = {
                "title": "🔔 Price Alert",
                "description": f"Price level reached for **{alert_data['symbol']}**",
                "color": 15844367,  # Orange
                "fields": [
                    {
                        "name": "📊 Symbol",
                        "value": alert_data['symbol'],
                        "inline": True
                    },
                    {
                        "name": "💰 Target Price",
                        "value": f"${alert_data['target_price']:.2f}",
                        "inline": True
                    },
                    {
                        "name": "💵 Current Price",
                        "value": f"${alert_data['current_price']:.2f}",
                        "inline": True
                    },
                    {
                        "name": "👤 User",
                        "value": username,
                        "inline": True
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "FVG Trading Platform - Price Alert"
                }
            }
            
            payload = {
                "embeds": [embed],
                "username": "FVG Trading Bot"
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return response.status_code in [200, 204]
            
        except Exception as e:
            print(f"Price alert notification failed: {str(e)}")
            return False
    
    def send_error_notification(self, webhook_url, user_id, error_message):
        """
        Send error notification to user
        """
        try:
            username = self._get_username(user_id)
            
            embed = {
                "title": "⚠️ Error Notification",
                "description": "An error occurred in your trading bot",
                "color": 15158332,  # Red
                "fields": [
                    {
                        "name": "👤 User",
                        "value": username,
                        "inline": False
                    },
                    {
                        "name": "❌ Error",
                        "value": error_message[:1000],  # Limit length
                        "inline": False
                    },
                    {
                        "name": "⏰ Time",
                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "FVG Trading Platform - Error Alert"
                }
            }
            
            payload = {
                "embeds": [embed],
                "username": "FVG Trading Bot"
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return response.status_code in [200, 204]
            
        except Exception as e:
            print(f"Error notification failed: {str(e)}")
            return False
    
    def _get_username(self, user_id):
        """
        Helper method to get username from database
        """
        try:
            user = self.db.get_user_by_id(user_id)
            if user:
                return user.get('username', 'Unknown')
            return 'Unknown'
        except:
            return 'Unknown'
    
    def validate_webhook_url(self, webhook_url):
        """
        Validate Discord webhook URL format
        """
        if not webhook_url:
            return False, "Webhook URL is empty"
        
        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            return False, "Invalid Discord webhook URL format"
        
        # Test the webhook
        try:
            response = requests.get(webhook_url, timeout=5)
            if response.status_code == 200:
                return True, "Webhook URL is valid"
            else:
                return False, f"Webhook validation failed: {response.status_code}"
        except Exception as e:
            return False, f"Webhook validation error: {str(e)}"
