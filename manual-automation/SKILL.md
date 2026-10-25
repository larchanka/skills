---
name: manual-automation
description: Manual browser testing and automation using Chrome DevTools MCP server. Handles port management, app launch, browser automation, login, and end-to-end testing.
---

# Manual Browser Automation

This skill enables manual browser testing and automation using the Chrome DevTools MCP server. It orchestrates the full workflow from port management through application launch, browser automation, login, and end-to-end testing.

## Workflow Execution Steps

### 1. Port Management

**Check if port 3000 is free:**
```bash
lsof -i :3000
```

**If port is in use:**
- Identify the process using the port
- Stop the existing application gracefully
- Verify the port is now free

**If port is free:**
- Proceed to application launch

### 2. Application Launch

**Launch the application in terminal:**
- Start the application server on port 3000
- Run in background mode to allow continued agent execution
- Monitor startup logs to ensure successful initialization
- Wait for the application to be ready (health check or expected log message)

### 3. Browser Automation Setup

**Initialize Chrome DevTools MCP connection:**
- Use MCP tools to connect to the browser
- Navigate to `http://localhost:3000`
- Wait for page load completion
- Take initial screenshot for documentation

### 4. Login Flow

**Execute login sequence:**
- Locate login form elements using MCP selectors
- Fill in credentials (use environment variables or secure storage)
- Submit the login form
- Wait for successful login redirect
- Verify login state (check for expected UI elements or cookies)
- Take screenshot of logged-in state

### 5. Testing Execution

**Perform end-to-end tests using MCP tools:**

Available MCP tool categories:
- **Input automation**: `click`, `type_text`, `fill`, `fill_form`, `hover`, `press_key`, `drag`, `upload_file`, `handle_dialog`, `click_at`
- **Navigation**: `navigate_page`, `new_page`, `select_page`, `close_page`, `list_pages`, `wait_for`
- **Emulation**: `emulate`, `resize_page`
- **Performance**: `performance_start_trace`, `performance_stop_trace`, `performance_analyze_insight`
- **Network**: `list_network_requests`, `get_network_request`
- **Debugging**: `take_screenshot`, `take_snapshot`, `evaluate_script`, `list_console_messages`, `get_console_message`, `lighthouse_audit`, `screencast_start`, `screencast_stop`

**Testing best practices:**
- Use `wait_for` to ensure elements are present before interaction
- Take screenshots at key test steps for documentation
- Check console messages for JavaScript errors
- Verify network requests complete successfully
- Use `evaluate_script` for custom assertions
- Run Lighthouse audits for performance and accessibility checks

### 6. Cleanup

**After testing completion:**
- Close browser pages/tabs
- Stop the application server
- Clean up any temporary files or data
- Report test results with screenshots and logs

## Exit Criteria

- Port 3000 is successfully managed (freed if needed)
- Application launches and runs without errors
- Browser successfully connects and navigates to the application
- Login flow completes successfully
- All specified test cases execute via MCP tools
- Test results are documented with screenshots and logs
- Application server is stopped and port is freed

## MCP Tool Reference

Key tools for testing:
- `navigate_page` - Navigate to URLs
- `click` - Click on elements
- `type_text` - Type text into inputs
- `fill` - Fill form fields
- `wait_for` - Wait for conditions
- `take_screenshot` - Capture screenshots
- `list_console_messages` - Check for errors
- `evaluate_script` - Run custom JavaScript
- `lighthouse_audit` - Performance/accessibility audits

## Error Handling

**Port conflicts:**
- If port cannot be freed, report error and suggest alternative port
- Document the process occupying the port for manual intervention

**Application launch failures:**
- Check application logs for errors
- Verify dependencies and configuration
- Report to user with specific error details

**Browser automation failures:**
- Use MCP debugging tools to diagnose issues
- Check console messages for JavaScript errors
- Verify element selectors are correct
- Take screenshots at failure points for debugging

**Login failures:**
- Verify credentials are correct
- Check for CAPTCHA or 2FA requirements
- Inspect network requests for authentication errors
- Report specific failure reason to user
