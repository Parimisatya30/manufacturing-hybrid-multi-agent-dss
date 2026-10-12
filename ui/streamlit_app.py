"""Decision-oriented Streamlit UI for the Manufacturing DSS."""

import uuid

import requests
import streamlit as st


st.set_page_config(
    page_title="Manufacturing DSS",
    page_icon="ðŸ­",
    layout="wide",
)

st.title("ðŸ­ Manufacturing Decision Support System")
st.caption(
    "Evidence-grounded manufacturing investigations "
    "with transparent findings and human oversight."
)


def first_value(*values):
    """Return the first non-empty value."""
    for value in values:
        if value is not None and value != "" and value != [] and value != {}:
            return value
    return None


def display_value(value):
    """Convert API values into readable text."""
    if isinstance(value, (dict, list)):
        return str(value)
    if value is None:
        return "Not available"
    return str(value)


def render_findings(findings):
    """Display findings as readable cards."""
    if not isinstance(findings, list) or not findings:
        st.info("No structured findings were returned.")
        return

    for index, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict):
            st.write(display_value(finding))
            continue

        severity = str(
            first_value(finding.get("severity"), finding.get("status"), "INFO")
        ).upper()

        heading = first_value(
            finding.get("finding"),
            finding.get("title"),
            finding.get("name"),
            f"Finding {index}",
        )

        with st.container(border=True):
            if severity in {"CRITICAL", "HIGH", "ERROR"}:
                st.error(f"**{heading}** Â· {severity}")
            elif severity in {"WARNING", "MEDIUM"}:
                st.warning(f"**{heading}** Â· {severity}")
            else:
                st.markdown(f"**{heading}** Â· {severity}")

            reason = first_value(
                finding.get("reason"),
                finding.get("description"),
                finding.get("explanation"),
            )
            if reason:
                st.write(reason)

            supporting = first_value(
                finding.get("supporting_evidence"),
                finding.get("source_ids"),
                finding.get("evidence"),
            )
            if supporting:
                st.caption(
                    "Supporting sources: " + display_value(supporting)
                )
def render_evidence(evidence):
    """Display evidence as readable tables or document passages."""

    if not isinstance(evidence, list) or not evidence:
        st.info("No supporting evidence was returned.")
        return

    for index, item in enumerate(evidence, start=1):
        if not isinstance(item, dict):
            st.write(str(item))
            continue

        source = first_value(
            item.get("source_id"),
            item.get("document_id"),
            item.get("source"),
            f"Evidence {index}",
        )

        metadata = item.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}

        source_type = str(
            first_value(metadata.get("source_type"), "unknown")
        ).lower()

        content = first_value(
            item.get("content"),
            item.get("description"),
            item.get("text"),
        )

        with st.expander(f"Evidence {index} Â· {source}"):
            st.caption(f"Source type: {source_type.upper()}")

            # SQL evidence: display returned records as a table.
            rows = metadata.get("rows")
            if isinstance(rows, list) and rows:
                st.markdown("**Returned records**")
                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )
            elif isinstance(rows, list):
                st.info("The SQL query returned no records.")

            # RAG or other textual evidence: display the source passage.
            if content and not (
                source_type == "sql"
                and "SQL query returned" in content
            ):
                st.markdown("**Supporting information**")
                st.write(content)
            elif source_type == "sql" and not rows:
                if content:
                    st.caption(content)

            # Show document provenance when available.
            document_id = metadata.get("document_id")
            if document_id:
                st.caption(f"Document: {document_id}")

            pages = metadata.get("page_numbers")
            if pages:
                st.caption(f"Page(s): {', '.join(map(str, pages))}")

            score = item.get("relevance_score")
            if score is not None:
                st.caption(f"Retrieval relevance: {score:.3f}")

def render_approval(approval):
    """Make approval requirements visible."""
    if not isinstance(approval, dict):
        return

    required = approval.get("required")
    status = first_value(approval.get("status"), "Not specified")
    reason = approval.get("reason")

    st.markdown("### Human approval")

    if required is True and str(status).upper() in {
        "PENDING", "REQUIRED", "AWAITING_APPROVAL"
    }:
        st.warning(f"Approval required Â· {status}")
    elif required is True:
        st.info(f"Approval required: {status}")
    elif required is False:
        st.success(f"Approval not required Â· {status}")
    else:
        st.write(f"Approval status: {status}")

    if reason:
        st.write(reason)


def render_result(workflow, result, request_id):
    """Render different workflow response shapes consistently."""
    decision = result.get("decision")
    response_data = result.get("response")

    decision = decision if isinstance(decision, dict) else {}
    response_data = (
        response_data if isinstance(response_data, dict) else {}
    )

    # Some workflows return fields at the top level, while maintenance
    # returns important fields under decision and response.
    status = first_value(
        response_data.get("overall_status"),
        decision.get("overall_status"),
        result.get("overall_status"),
        result.get("status"),
        result.get("severity"),
    )

    summary = first_value(
        response_data.get("summary"),
        result.get("summary"),
        result.get("llm_explanation"),
        response_data.get("llm_explanation"),
    )

    findings = first_value(
        response_data.get("findings"),
        decision.get("findings"),
        result.get("findings"),
        result.get("alerts"),
    )

    evidence = first_value(
        decision.get("evidence"),
        response_data.get("evidence"),
        result.get("evidence"),
    )

    data_gaps = first_value(
        response_data.get("data_gaps"),
        decision.get("data_gaps"),
        result.get("data_gaps"),
    )

    approval = first_value(
        response_data.get("approval"),
        decision.get("approval"),
        result.get("approval"),
    )

    st.subheader(f"{workflow} Â· Investigation Result")

    if status is not None:
        status_text = str(status).upper()
        if status_text == "EVIDENCE_AVAILABLE":
            st.info("Investigation status: Evidence available")
        elif status_text in {"CRITICAL", "FAILED", "ERROR"}:
            st.error(f"Overall status: {status_text}")
        elif status_text in {"WARNING", "DEGRADED"}:
            st.warning(f"Overall status: {status_text}")
        elif status_text in {"HEALTHY", "NORMAL", "SUCCESS"}:
            st.success(f"Overall status: {status_text}")
        else:
            st.info(f"Investigation status: {status_text}")

        # if status_text in {"CRITICAL", "FAILED", "ERROR"}:
        #     st.error(f"Overall status: {status_text}")
        # elif status_text in {"WARNING", "DEGRADED"}:
        #     st.warning(f"Overall status: {status_text}")
        # elif status_text in {"HEALTHY", "NORMAL", "SUCCESS"}:
        #     st.success(f"Overall status: {status_text}")
        # else:
        #     st.info(f"Overall status: {status_text}")

    if summary:
        st.markdown("### Summary")
        st.write(summary)

    # Show useful metrics when supplied by the API.
    metric_values = []
    for label, value in [
        ("Evidence items", first_value(
            decision.get("evidence_count"),
            response_data.get("evidence_count"),
            result.get("evidence_count"),
        )),
        ("Findings", len(findings) if isinstance(findings, list) else None),
        ("Approval", approval.get("status")
         if isinstance(approval, dict) else None),
    ]:
        if value is not None:
            metric_values.append((label, value))

    if metric_values:
        columns = st.columns(len(metric_values))
        for column, (label, value) in zip(columns, metric_values):
            column.metric(label, display_value(value))

    if findings is not None:
        st.markdown("### Key findings")
        render_findings(findings)

    if data_gaps:
        st.markdown("### Data gaps and limitations")
        if isinstance(data_gaps, list):
            for gap in data_gaps:
                st.warning(display_value(gap))
        else:
            st.warning(display_value(data_gaps))

    if evidence is not None:
        st.markdown("### Supporting evidence")
        render_evidence(evidence)

    render_approval(approval)

    # Show common workflow-specific fields without dumping the whole object.
    excluded = {
        "decision", "response", "findings", "evidence", "summary",
        "overall_status", "approval", "data_gaps", "llm_explanation",
        "evidence_count", "request_id",
    }
    extras = {
        key: value
        for key, value in result.items()
        if key not in excluded
    }

    if extras:
        with st.expander("Additional investigation details"):
            for key, value in extras.items():
                st.markdown(f"**{key.replace('_', ' ').title()}**")
                if isinstance(value, list) and key in {
                    "recommendations", "actions", "next_steps"
                }:
                    for item in value:
                        st.write(f"- {display_value(item)}")
                elif isinstance(value, (dict, list)):
                    st.write(value)
                else:
                    st.write(display_value(value))

    # with st.expander("Developer Details"):
    #     st.caption(f"Request ID: {request_id}")
    #     st.caption(f"HTTP status: 200")
    #     st.json(result, expanded=False)
    st.caption(f"Investigation reference: {request_id}")

api_base_url = "http://127.0.0.1:8000"


workflow = st.selectbox(
    "Choose an investigation",
    [
        "Predictive Maintenance",
        "Root Cause Analysis",
        "Defect Monitoring",
    ],
)

endpoint_map = {
    "Predictive Maintenance": "/api/v1/maintenance/investigate",
    "Root Cause Analysis": "/api/v1/rca/investigate",
    "Defect Monitoring": "/api/v1/defects/monitor",
}

with st.form("investigation_form"):
    machine_id = None

    if workflow == "Predictive Maintenance":
        machine_id = st.number_input(
            "Machine ID",
            min_value=1,
            value=8,
            step=1,
        )
        default_query = (
            "Assess the machine's current health, identify risks, "
            "and recommend evidence-supported next steps."
        )
    elif workflow == "Root Cause Analysis":
        default_query = (
            "Investigate the likely causes of recurring manufacturing "
            "defects. Distinguish confirmed evidence from hypotheses."
        )
    else:
        default_query = (
            "Summarize defect metrics, evaluate applicable thresholds, "
            "and identify limitations in the available data."
        )

    user_query = st.text_area(
        "Investigation question",
        value=default_query,
        max_chars=2000,
        height=110,
    )

    submitted = st.form_submit_button(
        "Run Investigation",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not api_base_url:
        st.error("Enter the FastAPI base URL in the sidebar.")
    elif not user_query.strip():
        st.error("Enter an investigation question.")
    else:
        request_id = str(uuid.uuid4())
        payload = {
            "user_query": user_query.strip(),
            "request_id": request_id,
        }

        if workflow == "Predictive Maintenance":
            payload["machine_id"] = int(machine_id)

        try:
            with st.spinner(
                f"Running {workflow.lower()}..."
            ):
                response = requests.post(
                    f"{api_base_url}{endpoint_map[workflow]}",
                    json=payload,
                    headers={"X-Request-ID": request_id},
                    timeout=(5, 180),
                )

            try:
                result = response.json()
            except ValueError:
                result = {"message": response.text}

            if response.ok and isinstance(result, dict):
                render_result(workflow, result, request_id)
            else:
                st.error(f"API request failed Â· HTTP {response.status_code}")
                st.write(result)
                st.caption(f"Request ID: {request_id}")

        except requests.exceptions.Timeout:
            st.error(
                "The request timed out. The backend may still be processing. "
                "Check the FastAPI logs before retrying."
            )
        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to FastAPI. Check the backend process "
                "and the base URL."
            )
        except requests.exceptions.RequestException as exc:
            st.error(f"Request failed: {exc}")

st.divider()
st.caption(
    "Review supporting evidence, data gaps, and approval requirements "
    "before acting on recommendations. The UI does not authorize "
    "manufacturing interventions."
)
