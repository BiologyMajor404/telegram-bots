# Roadmap

## Next portfolio projects: Claude / MCP integrations

Market check (Oct 2026): demand for Claude Code specialists on Fiverr +938% in half a year,
"AI integration" on Upwork +178%, about 825 "mcp server" gigs on Fiverr with few reviews.
Clients worry most about MCP security (tool poisoning, prompt injection, 30+ CVEs in early
2026), so both projects lead with least-privilege access, an action log and tests.

1. **MCP server for SlotBook.** Claude works with the real booking system: "who is booked
   tomorrow?", "move Anna to 15:00", "how much did I earn this week?". Read-only by default,
   changes only with explicit permission, every action logged.
2. **MCP server for Telegram.** Claude reads channels and chats, drafts and publishes posts,
   answers as a bot. Audience: bloggers, SMM managers, channel owners.
