from app.synthesis.response_generator import ResponseGenerator


def test_generates_response_with_evidence_and_pending_approval():
    generator = ResponseGenerator()

    decision = {
        "request_id": "request-1",
        "machine_id": 8,
        "overall_status": "CRITICAL",
        "findings": [
            {
                "finding": "Machine is in breakdown",
                "severity": "CRITICAL",
                "reason": "Machine lookup reported breakdown status.",
                "source_ids": ["machine_lookup"],
            }
        ],
        "evidence": [
            {
                "source_id": "machine_lookup",
                "content": "Machine status is breakdown.",
            }
        ],
        "sensor_data_status": "UNAVAILABLE",
        "approval": {
            "required": True,
            "status": "PENDING",
            "reason": "Human approval is required.",
        },
    }

    response = generator.generate(decision)

    assert response["overall_status"] == "CRITICAL"
    assert response["findings"][0]["severity"] == "CRITICAL"
    assert response["findings"][0]["supporting_evidence"] == [
        "machine_lookup"
    ]
    assert response["findings"][0]["traceability_complete"] is True
    assert response["data_gaps"]
    assert response["approval"]["status"] == "PENDING"


def test_reports_missing_evidence_reference():
    generator = ResponseGenerator()

    decision = {
        "overall_status": "CRITICAL",
        "findings": [
            {
                "finding": "Machine is in breakdown",
                "severity": "CRITICAL",
                "source_ids": ["missing_source"],
            }
        ],
        "evidence": [],
    }

    response = generator.generate(decision)

    finding = response["findings"][0]

    assert finding["supporting_evidence"] == []
    assert finding["traceability_complete"] is False


def test_handles_empty_findings():
    generator = ResponseGenerator()

    response = generator.generate(
        {
            "overall_status": "NORMAL",
            "findings": [],
            "evidence": [],
        }
    )

    assert response["findings"] == []
    assert "No findings" in response["summary"]


def test_does_not_invent_vibration_data():
    generator = ResponseGenerator()

    response = generator.generate(
        {
            "overall_status": "CRITICAL",
            "findings": [],
            "evidence": [],
            "sensor_data_status": "UNAVAILABLE",
        }
    )

    assert any(
        "unavailable" in gap.lower()
        for gap in response["data_gaps"]
    )
    assert "vibration_readings" not in response