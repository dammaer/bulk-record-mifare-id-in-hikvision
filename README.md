# BULK RECORD MIFARE ID IN HIKVISION

## Overview
This script can bulk add mifare cards to Hikvision video intercom (or other device from Hikvision with internal mifare card reader) without manually adding them in the panel’s web interface, as well as without using Hikvision iVMS software. First of all, this is necessary when the mifare_id of the cards is already known and they need to be duplicated in video intercom.

<details>
<summary><b>Example of video intercom (DS-KV8113-WME1(C))</b></summary>
<img src="https://github.com/dammaer/bulk-record-mifare-id-in-hikvision/assets/75730199/10ba0ed5-1298-426b-a992-c21a16e850f6"/>
</details>

You can add mifare cards by first preparing a text file with mifare_id in hex format, then the script will create users with the name you specify, 5 cards in each user. Or each mifare card separately. It is also possible to completely clear all users with cards added to them.

<details>
<summary><b>Example</b></summary>
<img src="https://github.com/dammaer/bulk-record-mifare-id-in-hikvision/assets/75730199/9682a7fd-1eaf-47ab-a8c8-b78df5efe198"/>
<img src="https://github.com/dammaer/bulk-record-mifare-id-in-hikvision/assets/75730199/431c8dde-28e5-4b16-94ba-7f8058347940"/>
</details>