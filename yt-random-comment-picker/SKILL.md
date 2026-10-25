---
name: yt-random-comment-picker
description: Downloads YouTube video comments, filters to unique authors, and randomly selects one comment to return.
metadata:
   version: 1.0.0
---

# Random Comment Picker

This skill downloads comments from a YouTube video, filters them to keep only comments with unique authors (first occurrence wins), and randomly selects one comment to return with author and text.

## Skill Details

- **Name**: yt-random-comment-picker
- **Version**: 1.0.0
- **Description**: Downloads YouTube video comments, filters to unique authors, and randomly selects one comment to return.

## Usage

```bash
yt-random-comment-picker <youtube_video_url>
```

### Example

```bash
yt-random-comment-picker https://youtu.be/VIDEO_ID
```

## How It Works

1. **Download comments**: Uses `yt-dlp` to fetch the comment section from the specified YouTube video URL
2. **Extract top-level comments**: Filters to keep only top-level comments (not replies/thread comments)
3. **Filter unique authors**: Keeps only the first comment from each unique author (subsequent duplicates are removed)
4. **Random selection**: Uses Python's `random.choice()` to select one comment from the filtered list
5. **Output**: Displays the selected comment with author and text, plus JSON output for programmatic use

## Requirements

- `yt-dlp` must be installed and available in PATH
- Python 3.6+
- Internet access to fetch YouTube comments

## Output Format

### Human-readable:
```
Author: @username
Comment: <comment text>
```

### JSON (printed at end):
```json
{
  "author": "@username",
  "text": "<comment text>",
  "likes": 5
}
```

## Notes

- The skill may take 30-60 seconds to download and process comments depending on the video's comment count
- Only top-level comments are considered (replies/thread comments are filtered out)
- If multiple comments from the same author exist, only the first one encountered is kept
- The selection is truly random - each unique-author comment has equal probability of being selected
- Works with any YouTube video URL that has comments available