# Disc-Alerts

In stock alerts for certain Disc Golf websites.

Will also post to a Discord channel if configured.

## Setup

Copy the `urls.example.json` file and name it `urls.json`. Fill it out with the urls for the stores you want to get
alerts for.

Example:

```json
{
  "Disc Company One": {
    "Limited Edition": "https://disc.company.one/products/limited/",
    "Standard": "https://disc.company.one/products/standard"
  },
  "Disc Company Two": {
    "All": "https://disc.company.two/products/"
  }
}
```

**Note:** The first time the script runs it will just produce a `discs.json` file. The `discs.json` file allows deltas
to be determined. It is updated after every run.

### Discord

If you want discord notifications then you'll need to set these variables:

| Variable | Value |
| ---------|------ |
| DISCORD_KEY | Your Discord Bot Token |
| DISCORD_CHANNEL | The channel ID to post to |
