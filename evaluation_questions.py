
evaluation_tests = [
    {
        "id": 1,
        "question": "How can I check available disk space on Windows?",
        "expected_keywords": ["File Explorer", "PowerShell", "Get-Volume"],
        "test_type": "Direct question"
    },
    {
        "id": 2,
        "question": "What PowerShell command displays available disk space?",
        "expected_keywords": ["Get-Volume", "SizeRemaining"],
        "test_type": "Specific question"
    },
    {
        "id": 3,
        "question": "How can I configure a VPN connection on Windows?",
        "expected_keywords": [],
        "expected_max_distance": 0.75,
        "test_type": "Out-of-scope question"
    },
    {
        "id": 4,
        "question": "How do I check the remaining free space?",
        "expected_keywords": ["SizeRemaining", "free space"],
        "test_type": "Contextual question"
    },
    {
        "id": 5,
        "question": "How do I increase the size of a Windows partition?",
        "expected_keywords": ["resize partitions", "extend volumes", "approval"],
        "test_type": "Missing information"
    }
]
