#!/usr/bin/env python3
"""
Test script to validate member data validation function
"""

def is_valid_member_data(user_data):
    """Check if user data contains actual member information (not generated/fake data)"""
    try:
        username = user_data.get('username', '')
        account_age_formatted = user_data.get('account_age_formatted', '')
        user_id = user_data.get('user_id', 0)

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
        print(f"Error validating member data: {e}")
        # Default to False if validation fails
        return False

def test_member_validation():
    """Test the member data validation function"""

    # Test cases - Invalid member data (should return False)
    invalid_test_cases = [
        {
            'name': 'Generic new members notification',
            'data': {
                'user_id': 1752573253,
                'username': 'New Member(s) Online (+15)',
                'account_age_formatted': 'Unknown',
                'server_name': 'LTX Studio'
            }
        },
        {
            'name': 'Monitoring active notification',
            'data': {
                'user_id': 1234567890,
                'username': 'Monitoring Active: Test Server',
                'account_age_formatted': 'System Monitor',
                'server_name': 'Test Server'
            }
        },
        {
            'name': 'Unknown user',
            'data': {
                'user_id': 0,
                'username': 'Unknown User',
                'account_age_formatted': 'Unknown',
                'server_name': 'Test Server'
            }
        },
        {
            'name': 'Empty username',
            'data': {
                'user_id': 1234567890,
                'username': '',
                'account_age_formatted': '2 months',
                'server_name': 'Test Server'
            }
        },
        {
            'name': 'Generic new member pattern',
            'data': {
                'user_id': 1234567890,
                'username': 'New Member(s) Detected',
                'account_age_formatted': 'Unknown',
                'server_name': 'Test Server'
            }
        }
    ]

    # Test cases - Valid member data (should return True)
    valid_test_cases = [
        {
            'name': 'Real user with proper data',
            'data': {
                'user_id': 1362788254054613055,
                'username': 'solar0an#0',
                'display_name': '! Solar',
                'account_age_formatted': '2 months and 27 days',
                'server_name': 'Axiom'
            }
        },
        {
            'name': 'Another real user',
            'data': {
                'user_id': 987654321098765432,
                'username': 'testuser123',
                'account_age_formatted': '1 year and 5 days',
                'server_name': 'Test Server'
            }
        },
        {
            'name': 'User with short account age but real data',
            'data': {
                'user_id': 123456789012345678,
                'username': 'newbie_user',
                'account_age_formatted': '5 days',
                'server_name': 'Test Server'
            }
        }
    ]

    print("🧪 Testing Member Data Validation Function")
    print("=" * 50)

    # Test invalid cases
    print("\n❌ Testing INVALID member data (should return False):")
    all_invalid_passed = True
    for test_case in invalid_test_cases:
        result = is_valid_member_data(test_case['data'])
        status = "✅ PASS" if not result else "❌ FAIL"
        print(f"  {status} - {test_case['name']}: {result}")
        if result:  # Should be False
            all_invalid_passed = False

    # Test valid cases
    print("\n✅ Testing VALID member data (should return True):")
    all_valid_passed = True
    for test_case in valid_test_cases:
        result = is_valid_member_data(test_case['data'])
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_case['name']}: {result}")
        if not result:  # Should be True
            all_valid_passed = False

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"Invalid cases: {'✅ ALL PASSED' if all_invalid_passed else '❌ SOME FAILED'}")
    print(f"Valid cases: {'✅ ALL PASSED' if all_valid_passed else '❌ SOME FAILED'}")

    overall_success = all_invalid_passed and all_valid_passed
    print(f"Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ TESTS FAILED'}")

    if overall_success:
        print("\n🎉 Validation function is working correctly!")
        print("   - Generic/fake notifications will be filtered out")
        print("   - Real member data will be allowed through")
        print("   - Bot will only send DMs for actual member joins")
    else:
        print("\n⚠️  Some tests failed - validation function needs adjustment")

    return overall_success

if __name__ == "__main__":
    test_member_validation()
