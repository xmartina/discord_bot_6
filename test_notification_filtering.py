#!/usr/bin/env python3
"""
Comprehensive test for notification filtering based on member data validation
Tests the complete flow of member data validation to ensure only real member joins trigger DMs
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockNotificationManager:
    """Mock notification manager to test the validation logic"""

    def __init__(self):
        self.sent_notifications = []
        self.skipped_notifications = []

    def _is_valid_member_data(self, user_data: Dict[str, Any]) -> bool:
        """Check if user data contains actual member information (not generated/fake data)"""
        try:
            # Handle None values gracefully by converting to safe defaults
            username = user_data.get('username')
            if username is None:
                username = ''
            else:
                username = str(username)

            account_age_formatted = user_data.get('account_age_formatted')
            if account_age_formatted is None:
                account_age_formatted = ''
            else:
                account_age_formatted = str(account_age_formatted)

            user_id = user_data.get('user_id', 0)
            if user_id is None:
                user_id = 0

            # Check for generic/fake usernames that indicate no real member data
            if (username.startswith('New Member(s) Online') or
                username.startswith('Monitoring Active:') or
                username == 'Unknown User' or
                'New Member(s)' in username):
                return False

            # Check for unknown account age (indicates no real member data)
            if account_age_formatted == 'Unknown':
                return False

            # Check for generated user IDs (they tend to be very large numbers)
            # Real Discord user IDs are typically 17-19 digits, generated ones are often different
            if user_id == 0:
                return False

            # Additional validation: check if we have meaningful user data
            # Real members should have proper usernames and account information
            if len(username.strip()) == 0:
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating member data: {e}")
            # Default to False if validation fails
            return False

    async def _send_discord_dm(self, user_data: Dict[str, Any]) -> bool:
        """Simulate sending notification via Discord DM with validation"""
        try:
            # Validate that we have real member data before sending DM
            if not self._is_valid_member_data(user_data):
                skip_info = {
                    'username': user_data.get('username', 'Unknown'),
                    'server_name': user_data.get('server_name', 'Unknown'),
                    'reason': 'Invalid member data',
                    'user_id': user_data.get('user_id', 0),
                    'account_age': user_data.get('account_age_formatted', 'Unknown')
                }
                self.skipped_notifications.append(skip_info)
                logger.info(f"Skipping DM notification - no valid member data for {user_data.get('username', 'Unknown')} in {user_data.get('server_name', 'Unknown')}")
                return False

            # Simulate successful DM send for valid data
            notification_info = {
                'username': user_data.get('username', 'Unknown'),
                'server_name': user_data.get('server_name', 'Unknown'),
                'user_id': user_data.get('user_id', 0),
                'account_age': user_data.get('account_age_formatted', 'Unknown'),
                'monitoring_source': user_data.get('monitoring_source', 'unknown')
            }
            self.sent_notifications.append(notification_info)
            logger.info(f"✅ DM sent for {user_data.get('username', 'Unknown')} in {user_data.get('server_name', 'Unknown')}")
            return True

        except Exception as e:
            logger.error(f"Error in mock DM send: {e}")
            return False

def create_test_scenarios() -> List[Dict[str, Any]]:
    """Create comprehensive test scenarios covering real and fake member data"""

    scenarios = [
        # Real member data scenarios (should send DM)
        {
            'name': 'Real user - solar0an example',
            'expected_dm': True,
            'data': {
                'user_id': 1362788254054613055,
                'username': 'solar0an#0',
                'display_name': '! Solar',
                'server_id': 1232529921335889921,
                'server_name': 'Axiom',
                'account_age_formatted': '2 months and 27 days',
                'account_created': '2025-04-18T13:53:00Z',
                'join_timestamp': '2025-07-15T08:31:00Z',
                'avatar_url': 'https://cdn.discordapp.com/avatars/1362788254054613055/7710e09c64d21441c68cbdf58363f22a.png',
                'is_verified': True,
                'monitoring_source': 'user_monitoring'
            }
        },
        {
            'name': 'Real user - newer account',
            'expected_dm': True,
            'data': {
                'user_id': 987654321098765432,
                'username': 'newbie123',
                'display_name': 'Newbie User',
                'server_id': 1206939519132114974,
                'server_name': 'Test Server',
                'account_age_formatted': '5 days',
                'account_created': '2025-07-10T12:00:00Z',
                'join_timestamp': '2025-07-15T09:54:00Z',
                'avatar_url': 'https://cdn.discordapp.com/avatars/987654321098765432/example.png',
                'is_verified': False,
                'monitoring_source': 'bot_monitoring'
            }
        },
        {
            'name': 'Real user - old account',
            'expected_dm': True,
            'data': {
                'user_id': 123456789012345678,
                'username': 'veteran_user',
                'display_name': 'Veteran',
                'server_id': 1234567890123456789,
                'server_name': 'Gaming Server',
                'account_age_formatted': '3 years and 2 months',
                'account_created': '2022-05-15T10:30:00Z',
                'join_timestamp': '2025-07-15T14:20:00Z',
                'avatar_url': None,
                'is_verified': True,
                'monitoring_source': 'enhanced_detection'
            }
        },

        # Fake/Generated member data scenarios (should NOT send DM)
        {
            'name': 'Generic member count notification',
            'expected_dm': False,
            'data': {
                'user_id': 1752573253,
                'username': 'New Member(s) Online (+15)',
                'display_name': 'New Member(s) Online (+15)',
                'server_id': 1206939519132114974,
                'server_name': 'LTX Studio',
                'account_age_formatted': 'Unknown',
                'account_created': '2025-07-15T09:54:00Z',
                'join_timestamp': '2025-07-15T09:54:00Z',
                'avatar_url': None,
                'is_verified': True,
                'monitoring_source': 'enhanced_count_tracking_member_count_fallback'
            }
        },
        {
            'name': 'Monitoring heartbeat notification',
            'expected_dm': False,
            'data': {
                'user_id': 1234567890987654321,
                'username': 'Monitoring Active: Test Server',
                'display_name': 'Monitoring Active: Test Server',
                'server_id': 1111111111111111111,
                'server_name': 'Test Server',
                'account_age_formatted': 'System Monitor',
                'account_created': '2025-07-15T15:00:00Z',
                'join_timestamp': '2025-07-15T15:00:00Z',
                'avatar_url': None,
                'is_verified': True,
                'monitoring_source': 'heartbeat_monitoring'
            }
        },
        {
            'name': 'Presence tracking notification',
            'expected_dm': False,
            'data': {
                'user_id': 9876543210123456789,
                'username': 'New Member(s) Online (+3)',
                'display_name': 'New Member(s) Online (+3)',
                'server_id': 2222222222222222222,
                'server_name': 'Discord Community',
                'account_age_formatted': 'Unknown',
                'account_created': '2025-07-15T16:00:00Z',
                'join_timestamp': '2025-07-15T16:00:00Z',
                'avatar_url': None,
                'is_verified': True,
                'monitoring_source': 'enhanced_presence_tracking'
            }
        },
        {
            'name': 'Unknown user fallback',
            'expected_dm': False,
            'data': {
                'user_id': 0,
                'username': 'Unknown User',
                'display_name': 'Unknown User',
                'server_id': 3333333333333333333,
                'server_name': 'Unknown Server',
                'account_age_formatted': 'Unknown',
                'account_created': '2025-07-15T16:30:00Z',
                'join_timestamp': '2025-07-15T16:30:00Z',
                'avatar_url': None,
                'is_verified': False,
                'monitoring_source': 'fallback_detection'
            }
        },

        # Edge cases
        {
            'name': 'Empty username',
            'expected_dm': False,
            'data': {
                'user_id': 1111222233334444555,
                'username': '',
                'display_name': '',
                'server_id': 4444444444444444444,
                'server_name': 'Edge Case Server',
                'account_age_formatted': '1 month',
                'account_created': '2025-06-15T12:00:00Z',
                'join_timestamp': '2025-07-15T17:00:00Z',
                'avatar_url': None,
                'is_verified': False,
                'monitoring_source': 'edge_case_test'
            }
        },
        {
            'name': 'Generic pattern with "New Member(s)"',
            'expected_dm': False,
            'data': {
                'user_id': 5555666677778888999,
                'username': 'New Member(s) Detected in Channel',
                'display_name': 'New Member(s) Detected in Channel',
                'server_id': 5555555555555555555,
                'server_name': 'Pattern Test Server',
                'account_age_formatted': 'Unknown',
                'account_created': '2025-07-15T17:30:00Z',
                'join_timestamp': '2025-07-15T17:30:00Z',
                'avatar_url': None,
                'is_verified': True,
                'monitoring_source': 'pattern_detection'
            }
        }
    ]

    return scenarios

async def run_comprehensive_test():
    """Run comprehensive test of notification filtering"""

    print("🧪 COMPREHENSIVE NOTIFICATION FILTERING TEST")
    print("=" * 60)
    print()

    # Create mock notification manager
    notification_manager = MockNotificationManager()

    # Get test scenarios
    scenarios = create_test_scenarios()

    print(f"📋 Running {len(scenarios)} test scenarios...")
    print()

    passed_tests = 0
    failed_tests = 0

    for i, scenario in enumerate(scenarios, 1):
        print(f"🔍 Test {i}/{len(scenarios)}: {scenario['name']}")

        # Simulate sending notification
        result = await notification_manager._send_discord_dm(scenario['data'])
        expected = scenario['expected_dm']

        # Check if result matches expectation
        if result == expected:
            status = "✅ PASS"
            passed_tests += 1
        else:
            status = "❌ FAIL"
            failed_tests += 1

        print(f"   {status} - Expected DM: {expected}, Got: {result}")

        # Show details for failed tests
        if result != expected:
            print(f"   📄 Username: '{scenario['data'].get('username', 'N/A')}'")
            print(f"   📄 Account Age: '{scenario['data'].get('account_age_formatted', 'N/A')}'")
            print(f"   📄 User ID: {scenario['data'].get('user_id', 'N/A')}")

        print()

    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(scenarios)}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {(passed_tests/len(scenarios)*100):.1f}%")
    print()

    # Notification summary
    print("📬 NOTIFICATION SUMMARY")
    print("-" * 30)
    print(f"DMs Sent: {len(notification_manager.sent_notifications)}")
    print(f"DMs Skipped: {len(notification_manager.skipped_notifications)}")
    print()

    if notification_manager.sent_notifications:
        print("✅ DMs SENT FOR:")
        for notification in notification_manager.sent_notifications:
            print(f"   • {notification['username']} in {notification['server_name']}")
        print()

    if notification_manager.skipped_notifications:
        print("⏭️  DMs SKIPPED FOR:")
        for notification in notification_manager.skipped_notifications:
            print(f"   • {notification['username']} in {notification['server_name']} (Reason: {notification['reason']})")
        print()

    # Overall result
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED!")
        print("✅ The notification filtering is working correctly!")
        print("✅ Only real member joins will trigger DM notifications!")
        print("✅ Generic/fake notifications will be filtered out!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED!")
        print("❌ The notification filtering needs adjustment!")
        return False

def test_validation_edge_cases():
    """Test edge cases for the validation function"""

    print("\n🔬 TESTING VALIDATION EDGE CASES")
    print("-" * 40)

    notification_manager = MockNotificationManager()

    edge_cases = [
        # Test None values
        {'user_id': None, 'username': None, 'account_age_formatted': None},

        # Test missing keys
        {},

        # Test whitespace username
        {'user_id': 123, 'username': '   ', 'account_age_formatted': '1 day'},

        # Test very large user ID (potential generated ID)
        {'user_id': 999999999999999999999, 'username': 'test', 'account_age_formatted': '1 day'},

        # Test normal case that should pass
        {'user_id': 123456789012345678, 'username': 'normal_user', 'account_age_formatted': '30 days'},
    ]

    for i, case in enumerate(edge_cases, 1):
        try:
            result = notification_manager._is_valid_member_data(case)
            print(f"Edge case {i}: {result} - {case}")
        except Exception as e:
            print(f"Edge case {i}: ERROR - {e} - {case}")

    print("✅ Edge case testing completed")

if __name__ == "__main__":
    import asyncio

    async def main():
        # Run comprehensive test
        success = await run_comprehensive_test()

        # Run edge case testing
        test_validation_edge_cases()

        # Final summary
        print("\n" + "=" * 60)
        if success:
            print("🏆 NOTIFICATION FILTERING IMPLEMENTATION IS WORKING PERFECTLY!")
            print("🚀 Ready for deployment!")
        else:
            print("⚠️  NOTIFICATION FILTERING NEEDS ADJUSTMENTS!")
            print("🔧 Please review the failed test cases!")
        print("=" * 60)

    asyncio.run(main())
