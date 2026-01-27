# Web Search Implementation

This document provides a comparison of web search API providers and a decision checklist for selecting the appropriate provider for the Discord bot.

## API Provider Comparison

### Brave Search API

**Overview:**
Brave Search API provides privacy-focused web search results with a simple REST API.

**Pros:**
- Fast response times
- Privacy-focused (no user tracking)
- Good quality search results
- Reasonable pricing with free tier
- Simple API with straightforward authentication
- No complex setup required
- Reliable uptime and performance

**Cons:**
- Requires API key (sign up needed)
- Rate limits on free tier
- Limited to web search (no specialized search types)

**Pricing:**
- Free tier: 2,000 queries/month
- Paid plans: Starting at $5/month for 15,000 queries
- Pay-as-you-go option available

**API Details:**
- Endpoint: `https://api.search.brave.com/res/v1/web/search`
- Authentication: `X-Subscription-Token` header
- Rate limit: Varies by plan
- Documentation: https://brave.com/search/api/

**Best for:**
- General web search
- Privacy-conscious applications
- Projects with moderate search volume
- Teams wanting simple integration

---

### Tavily API

**Overview:**
Tavily is an AI-optimized search API designed specifically for research and AI applications.

**Pros:**
- AI-optimized results (better for LLM consumption)
- Good for research and fact-checking
- Structured data extraction
- Free tier available
- Designed for AI agents and chatbots

**Cons:**
- Newer service (less established than competitors)
- Smaller index compared to major search engines
- Limited documentation and community support
- May have reliability concerns due to being newer

**Pricing:**
- Free tier: 1,000 queries/month
- Paid plans: Custom pricing based on usage
- Enterprise options available

**API Details:**
- Endpoint: Custom API endpoint
- Authentication: API key
- Rate limit: Varies by plan
- Documentation: https://tavily.com/

**Best for:**
- AI-powered research applications
- Fact-checking and verification
- Projects requiring structured data extraction
- Teams building AI agents

---

### SerpAPI

**Overview:**
SerpAPI provides access to multiple search engines (Google, Bing, Yahoo, etc.) through a unified API.

**Pros:**
- Supports multiple search engines (Google, Bing, Yahoo, Baidu, etc.)
- Comprehensive search types (web, images, news, shopping, etc.)
- Well-established service with good reliability
- Extensive documentation and examples
- Handles CAPTCHA and rate limiting automatically

**Cons:**
- More expensive than alternatives
- Complex API with many options (steeper learning curve)
- Overkill for simple web search use cases
- Higher cost per query

**Pricing:**
- Free tier: 100 queries/month
- Paid plans: Starting at $50/month for 5,000 queries
- Pay-per-query pricing available
- Enterprise plans for high volume

**API Details:**
- Endpoint: `https://serpapi.com/search`
- Authentication: API key parameter
- Rate limit: Varies by plan
- Documentation: https://serpapi.com/

**Best for:**
- Multi-engine search requirements
- Complex search types (images, news, shopping)
- Enterprise applications with high budgets
- Projects requiring Google search results specifically

---

## Implementation Status

### Currently Implemented
- **Brave Search API**: Fully implemented in `bot/services/web_search.py`
  - `BraveSearchClient` class with async context manager
  - Error handling and response parsing
  - Integration with Discord bot via `/web-search` command

### Placeholder Implementations
- **Tavily API**: Class structure exists, raises `NotImplementedError`
- **SerpAPI**: Class structure exists, raises `NotImplementedError`

### Factory Pattern
The `create_client()` factory function in `bot/services/web_search.py` supports all three providers:
```python
client = create_client(api_type="brave", api_key="your_key")
```

To switch providers, update the `WEB_SEARCH_API_TYPE` environment variable.

---

## Team Decision Checklist

Use this checklist to select the appropriate web search provider for your project.

### Requirements Analysis

- [ ] **Search Volume**: How many searches per month do you expect?
  - Low (< 1,000): Any provider works
  - Medium (1,000 - 10,000): Brave or Tavily
  - High (> 10,000): Consider budget and choose accordingly

- [ ] **Budget**: What's your monthly budget for search API?
  - $0: Brave (2,000/month) or Tavily (1,000/month)
  - $5-50: Brave paid plans
  - $50+: SerpAPI or Brave enterprise

- [ ] **Use Case**: What type of search do you need?
  - General web search: Brave (recommended)
  - AI research/fact-checking: Tavily
  - Multi-engine or specialized search: SerpAPI

- [ ] **Privacy Requirements**: Do you need privacy-focused search?
  - Yes: Brave (privacy-first)
  - No: Any provider works

- [ ] **Integration Complexity**: How much time can you spend on integration?
  - Minimal: Brave (simplest API)
  - Moderate: Tavily
  - Complex: SerpAPI (most features, most complex)

### Technical Considerations

- [ ] **API Reliability**: Do you need proven uptime?
  - Critical: Brave or SerpAPI (established)
  - Moderate: Tavily (newer but growing)

- [ ] **Documentation Quality**: Do you need extensive docs and examples?
  - Yes: SerpAPI (most comprehensive)
  - Moderate: Brave (good docs)
  - Basic: Tavily (limited docs)

- [ ] **Rate Limiting**: Can you handle rate limits?
  - Yes: Any provider (implement backoff/retry)
  - No: Choose higher tier plan

- [ ] **Response Format**: Do you need structured data?
  - Yes: Tavily (AI-optimized) or SerpAPI (comprehensive)
  - No: Brave (simple JSON)

### Recommendation Matrix

| Scenario | Recommended Provider | Reason |
|----------|---------------------|--------|
| Discord bot with moderate usage | **Brave** | Simple, fast, good free tier |
| AI research assistant | **Tavily** | AI-optimized results |
| Enterprise multi-search app | **SerpAPI** | Multiple engines, comprehensive |
| Privacy-focused application | **Brave** | Privacy-first approach |
| Budget-constrained project | **Brave** or **Tavily** | Best free tiers |
| High-volume commercial app | **SerpAPI** | Scalable, reliable |

### Current Project Decision

**Selected Provider:** Brave Search API

**Rationale:**
- Discord bot use case (moderate search volume)
- Simple integration requirements
- Good free tier (2,000 queries/month)
- Privacy-focused aligns with user expectations
- Fast response times for real-time Discord interactions
- Well-documented and reliable

**Configuration:**
```env
WEB_SEARCH_API_TYPE=brave
WEB_SEARCH_API_KEY=your_brave_api_key_here
```

**Next Steps:**
1. Sign up for Brave Search API: https://brave.com/search/api/
2. Get API key from dashboard
3. Add API key to `.env` file
4. Test `/web-search` command in Discord
5. Monitor usage and upgrade plan if needed

---

## Migration Guide

If you need to switch providers in the future:

1. **Update Environment Variables:**
   ```env
   WEB_SEARCH_API_TYPE=tavily  # or serpapi
   WEB_SEARCH_API_KEY=new_api_key
   ```

2. **Implement Provider Class:**
   - Edit `bot/services/web_search.py`
   - Replace `NotImplementedError` with actual implementation
   - Follow the `WebSearchClient` abstract base class interface

3. **Test Integration:**
   ```bash
   # Test new provider
   uv run python -c "from bot.services.web_search import create_client; ..."
   ```

4. **Deploy:**
   - Update `.env` in production
   - Restart bot service
   - Monitor for errors

---

## Additional Resources

- **Brave Search API**: https://brave.com/search/api/
- **Tavily API**: https://tavily.com/
- **SerpAPI**: https://serpapi.com/
- **Implementation Code**: `bot/services/web_search.py`
- **Discord Command**: `bot/cogs/websearch.py`
