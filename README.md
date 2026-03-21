# SmithAI

**Enterprise-grade AI Agent Framework** for browser automation, web scraping, and intelligent task orchestration.

---

## What SmithAI Does

SmithAI is built for real enterprise workflows - not demos. It handles the complex, messy work that actual businesses need:

| Problem | How SmithAI Solves It |
|---------|----------------------|
| **Web scraping gets blocked** | Stealth browser with anti-detection bypasses Cloudflare, Imperva, and bot checks |
| **CAPTCHAs stop automation** | Automatic captcha detection and solving via 2Captcha/Anti-Captcha |
| **Multiple accounts management** | Browser pools with isolated profiles and proxy rotation |
| **Manual data entry** | Agents fill forms, extract data, and update systems automatically |
| **Cross-team coordination** | Crew AI orchestrates specialized agents for complex workflows |
| **Remote browser access** | Chrome DevTools Protocol for distributed automation |

---

## Core Capabilities

### Browser Automation (The Enterprise Way)

```python
from smith_ai.browser.stealth import StealthBrowser, DetectionLevel, HumanBehavior
from smith_ai.captcha import CaptchaAutomation

# Stealth browser that looks like a real user
browser = StealthBrowser(DetectionLevel.MAXIMUM)
await browser.launch()

# Navigate and handle captchas automatically
await browser.navigate("https://example.com/secure-form")
await CaptchaAutomation(browser).handle_captcha(browser._page)

# Human-like typing and clicking
await HumanBehavior.human_type(browser, "#email", "user@example.com")
await HumanBehavior.human_click(browser, "#submit")
```

### Anti-Detection Features

- Randomized user agents and viewport sizes
- Canvas/WebGL fingerprint spoofing
- Timezone and language randomization
- Proxy rotation support
- Human-like mouse movements and typing patterns
- Automatic cookie and session management

### Multi-Agent Orchestration

```python
from smith_ai import Agent, Task, Crew, Process, create_llm

llm = create_llm("nvidia", model="nvidia/nemotron-3-super-120b-a12b")

researcher = Agent(name="Researcher", role="researcher", goal="Find leads", llm=llm)
validator = Agent(name="Validator", role="validator", goal="Verify data", llm=llm)
enricher = Agent(name="Enricher", role="enricher", goal="Add company data", llm=llm)

crew = Crew(
    agents=[researcher, validator, enricher],
    tasks=[
        Task(description="Find 100 tech company contacts", agent_name="Researcher"),
        Task(description="Verify email addresses", agent_name="Validator"),
        Task(description="Add LinkedIn and company info", agent_name="Enricher"),
    ],
    process=Process.SEQUENTIAL,
)

result = await crew.kickoff()
```

### Remote Browser Mode

```python
from smith_ai.browser.remote import RemoteBrowser, BrowserPool, BrowserType

# Connect to existing Chrome for debugging
browser = RemoteBrowser()
await browser.connect()

# Or launch dedicated browser instances
browser = await RemoteBrowser.launch(
    headless=True,
    proxy="socks5://proxy.example.com:1080",
    user_data_dir="/tmp/chrome-profile"
)

# Scale with browser pools for parallel work
pool = BrowserPool(size=10, browser_type=BrowserType.CHROMIUM, headless=True)
await pool.start()

result = await pool.execute_task(lambda b: scrape_leads(b))
```

---

## Integrations

### GitHub - Automate Development Workflows

```python
from smith_ai.integrations import GitHubClient, GitHubConfig

github = GitHubClient(GitHubConfig(token="ghp_xxx"))

# Auto-triage issues
issues = await github.list_issues(state="open", labels=["bug","priority"])
for issue in issues:
    if "urgent" in issue["title"].lower():
        await github.add_comment(issue["number"], "Triaging as P0...")
        await github.update_issue(issue["number"], labels=["P0","urgent"])

# Create PRs with release notes
await github.create_pr(
    title="Release v2.0.0",
    head="release/2.0.0",
    base="main",
    body="## What's New\n- Feature 1\n- Feature 2"
)
```

### Slack - Team Notifications

```python
from smith_ai.integrations import SlackClient, SlackWebhook

# Direct API for full control
slack = SlackClient(SlackWebhook("https://hooks.slack.com/services/xxx"))
await slack.post_message(
    channel="#alerts",
    text="Deployment complete",
    blocks=[{
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Deploy Successful*\nVersion 2.0 deployed to production"}
    }]
)

# Simple webhook for alerts
webhook = SlackWebhook("https://hooks.slack.com/services/xxx")
await webhook.send("Daily report: 150 leads processed, 23 conversions")
```

### Notion - Knowledge Management

```python
from smith_ai.integrations import NotionClient, NotionBlockBuilder

notion = NotionClient()

# Create project pages from agent output
page = await notion.create_page(
    parent_id="parent-page-id",
    properties={"title": {"title": [{"text": {"content": "Q4 Roadmap"}}]}},
    children=[
        NotionBlockBuilder.heading("Goals", 1),
        NotionBlockBuilder.paragraph("Increase MRR by 40%"),
        NotionBlockBuilder.bulleted_list_item("Launch enterprise tier"),
        NotionBlockBuilder.bulleted_list_item("Expand to APAC"),
        NotionBlockBuilder.code_block("SELECT * FROM revenue WHERE quarter = 'Q4'", "sql"),
    ]
)
```

### Jira - Project Tracking

```python
from smith_ai.integrations import JiraClient

jira = JiraClient()

# Sprint management
sprints = await jira.get_sprints(board_id="123", state="active")
active_sprint = sprints[0]

# Create tasks from customer feedback
feedback = await github.search_issues(query="type:issue label:customer-feedback")
for issue in feedback["items"][:5]:
    await jira.create_issue(
        project_key="PROD",
        issue_type="Task",
        summary=f"[From GitHub] {issue['title']}",
        description=issue["body"],
        priority="High",
        labels=["customer-feedback", "ai-generated"]
    )
```

### Google Workspace - Enterprise Productivity

```python
from smith_ai.integrations import GmailTool, CalendarTool, DriveTool

gmail = GmailTool()
calendar = CalendarTool()
drive = DriveTool()

# Send daily summaries
await gmail.send_email(
    to="team@company.com",
    subject="Daily AI Report",
    body="Generated 500 leads, qualified 120, scheduled 15 demos"
)

# Schedule meetings
await calendar.create_event(
    summary="Sales Demo",
    start_time="2024-01-15T14:00:00Z",
    end_time="2024-01-15T15:00:00Z",
    attendees=["client@example.com", "sales@company.com"]
)

# Upload reports to Drive
with open("weekly-report.pdf", "rb") as f:
    await drive.upload_file(name="Weekly Report.pdf", content=f.read())
```

---

## Real-World Use Cases

### Lead Generation at Scale

```python
# 1. Use stealth browser to scrape LinkedIn without detection
# 2. Crew of agents: Researcher → Validator → Enricher → Loader
# 3. Auto-create HubSpot contacts via API
# 4. Schedule follow-up sequences in Calendly
# 5. Send personalized outreach via Gmail
```

### Competitor Monitoring

```python
# 1. Stealth browser monitors 50 competitor sites
# 2. Agent tracks pricing changes, new features, blog posts
# 3. Alerts via Slack when significant changes detected
# 4. Auto-update Notion database with findings
# 5. Generate weekly competitive intelligence reports
```

### Customer Support Automation

```python
# 1. Monitor incoming tickets via Zendesk API
# 2. Agent reads ticket, searches knowledge base
# 3. Drafts response and suggests solutions
# 4. Human agent approves and sends
# 5. Agent learns from resolved tickets
```

### Regression Testing

```python
# 1. Browser pool runs 20 browsers in parallel
# 2. Each navigates different test scenarios
# 3. Captures screenshots on failures
# 4. Uploads results to Jira with screenshots
# 5. Notifies team via Slack
```

---

## Installation

```bash
# Core (tools, agents, basic browser)
pip install smith-ai

# With LLM providers
pip install smith-ai[llm]

# With browser automation
pip install smith-ai[browser]

# Full stealth mode (anti-detection)
pip install smith-ai[stealth]

# With all integrations
pip install smith-ai[all]
```

---

## Architecture

```
smith_ai/
├── core/              # Types, interfaces, base classes
├── llm/               # 10 LLM providers (OpenAI, Anthropic, Google, NVIDIA, etc.)
├── tools/             # 15+ built-in tools + @tool decorator
├── agents/            # Agent with tool support
├── crew/              # Multi-agent orchestration
├── runtime/            # Execution environment
├── browser/           # Browser automation
│   ├── stealth/      # Anti-detection browser
│   ├── remote/       # Remote Chrome via CDP
│   └── cdp/          # Chrome DevTools Protocol
├── captcha/           # reCAPTCHA, hCaptcha, Turnstile solving
├── tui/               # Terminal UI (Claude Code style)
└── integrations/      # GitHub, Slack, Discord, Notion, Jira, Google
```

---

## Enterprise Features

- **SOC 2 Ready**: Audit logging, role-based access
- **Scalable**: Browser pools, distributed execution
- **Secure**: Encrypted credentials, secrets management
- **Reliable**: Retry logic, circuit breakers, dead letter queues
- **Observable**: Structured logging, metrics, tracing

---

## License

MIT - Himan D <himanshu@open.ai>
