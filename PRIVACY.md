# Plain Science Uploader – Privacy Policy

Applies to the internal upload script of the YouTube channel **Plain Science** (Google Cloud project 688170251974).
Owner: Gowrishankar Kolli, Roding, Germany · Contact: gowrishankarkolli15@gmail.com · Last updated: 12 November 2026

## 1. What this tool is

Plain Science Uploader (`upload.py` in this repository) is a private, single-user Python script that uses **YouTube API Services** to upload the owner's own original science videos to the owner's own YouTube channel. It has no public interface, no sign-ups and no other users.

## 2. YouTube API Services and Google Privacy Policy

This tool uses YouTube API Services. By using it you agree to the [YouTube Terms of Service](https://www.youtube.com/t/terms). Google's handling of data is described in the [Google Privacy Policy](http://www.google.com/policies/privacy).

## 3. Data accessed and how it is used

- OAuth 2.0 scopes: `youtube.upload` (to upload the owner's videos) and `youtube.readonly` (to read titles of the owner's own uploads, to avoid repeating topics).
- Endpoints: `videos.insert`, `search.list` (forMine=true), `videos.list` (own videos only).
- No data from any other YouTube user is accessed, collected, displayed or shared. No content is downloaded.

## 4. Storage, sharing and deletion

- No YouTube API data is stored beyond a single script run, and nothing is shared with third parties. No cookies or tracking are used.
- The OAuth token is kept only on the owner's own computer and can be deleted at any time by deleting the token file.
- Access can be revoked at any time at https://security.google.com/settings/security/permissions

## 5. Contact

Questions about this policy: gowrishankarkolli15@gmail.com

See also: [Terms of Service](TERMS.md)
