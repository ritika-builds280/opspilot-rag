evaluation_tests = [
    {
        "id": 1,
        "question": "How can I check available disk space on Windows?",
        "expected_topic": "File Explorer and PowerShell methods",
        "test_type": "Direct question"
    },
    {
        "id": 2,
        "question": "What PowerShell command displays available disk space?",
        "expected_topic": "Get-Volume command",
        "test_type": "Specific question"
    },
    {
        "id": 3,
        "question": "How can I configure a VPN connection on Windows?",
        "expected_topic": "Information not available",
        "test_type": "Out-of-scope question"
    },
    {
        "id": 4,
        "question": "How do I check the remaining free space?",
        "expected_topic": "Available disk space",
        "test_type": "Contextual question"
    },
    {
        "id": 5,
        "question": "How do I increase the size of a Windows partition?",
        "expected_topic": "Information not available unless documented",
        "test_type": "Missing information"
    }
]