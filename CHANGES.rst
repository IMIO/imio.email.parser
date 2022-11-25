Changelog
=========


0.2 (unreleased)
----------------

- Removed newline characters from attachement filename causing exception when creating file later in Plone.
  [sgeulette]
- Added attachments information
  [sgeulette]
- Corrected attachments disposition (check really embedded content ids)
  [sgeulette]
- Worked with EmailMessage
  [sgeulette]
- Added specific handling for Apple Mail forward
  [sgeulette]

0.1 (2022-02-17)
----------------

- Corrected badly addresses from email.utils.getAddresses
- Managed email2pdf exception when email body is empty
- Added tests
- Added headers in pdf
- Added emailtopdf script to test easily eml transformation in pdf
- Initial release.
  [laulaz, sgeulette]
