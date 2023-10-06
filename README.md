# BULK RECORD MIFARE ID IN HIKVISION

## Overview
This script can bulk add mifare cards to Hikvision video intercom (or other device from Hikvision with internal mifare card reader) without manually adding them in the panel’s web interface, as well as without using Hikvision iVMS software. First of all, this is necessary when the mifare_id of the cards is already known and they need to be duplicated in video intercom.

<details>
<summary><b>Example of video intercom DS-KV8113-WME1(C)</b></summary>
<img src="https://github.com/dammaer/bulk-record-mifare-id-in-hikvision/assets/75730199/10ba0ed5-1298-426b-a992-c21a16e850f6"/>
</details>

You can add mifare cards by first preparing a text file with mifare_id in hex format, then the script will create users with the name you specify, 5 cards in each user. Or each mifare card separately. It is also possible to completely clear all users with cards added to them.

<details>
<summary><b>Example</b></summary>
<img src="https://github.com/dammaer/bulk-record-mifare-id-in-hikvision/assets/75730199/9682a7fd-1eaf-47ab-a8c8-b78df5efe198"/>
<img src="https://github.com/dammaer/bulk-record-mifare-id-in-hikvision/assets/75730199/431c8dde-28e5-4b16-94ba-7f8058347940"/>
</details>

## Installation
Requires Python 3.10+ to run correctly!
```bash
# Clone this repository or download the zip file
git clone https://github.com/dammaer/bulk-record-mifare-id-in-hikvision.git
# Go to the folder
cd bulk-record-mifare-id-in-hikvision/
# Creation and activation of virtual environment
python3 -m venv venv
source venv/bin/activate
# Installing required packages
pip install -r requirements.txt
```

## Usage
Prepare the **settings.ini** file. Indicate in it the IP addresses of video intercom stations and the login and password for them.

### :small_blue_diamond: Adding new mifare_id or updating existing ones from a file
```bash
# Run the script with the -u add.txt and -n student keys. 
# This will update or create users named student1, student2, etc. and add 5 mifare cards to each.
python record_mifare_id.py -u add.txt -n student
```
<details>
<summary><b>Example file with mifare_id cards in hex format</b></summary>
<img src="https://github.com/dammaer/bulk-record-mifare-id-in-hikvision/assets/75730199/baffb306-67bf-4125-a6c3-2ff6f4fe59ef"/>
</details>

### :small_blue_diamond: Adding new mifare_id as argument value
```bash
# This will add new mifare cards to existing users called student 
# or create a new user student if the remaining users are full
python record_mifare_id.py -a 85EF77B4 7290FDE1 -n student
```
### :small_blue_diamond: Removing all users and their mifare cards
```bash
# This will remove all users with the name "student" and their mifare cards
python record_mifare_id.py -c -n student
```
### :warning: Note on mifare key hex
Some mifare card readers display the key value in reverse. For example, the NFC Tool (Android) application displays the 85EF77B4 key as 4B:77:FE:58 when read. This must be taken into account before use, otherwise mifare cards will not work!