# BloodHound_CustomQueries_Toolset

Tool to import your customqueries for [BloodHound "Legacy"](https://github.com/BloodHoundAD/BloodHound) to [BloodHound "Community"](https://github.com/SpecterOps/BloodHound).

note: on linux/kali, your customqueries.json file for BloodHound Legacy is located at `~/.config/bloodhound/customqueries.json`

## Installation

1. Clone this repository.
2. Copy the `example.env` file to `.env` and fill in the required environment variables.
3. Install the required packages:

```bash
pip3 install -r requirements.txt
```

## Environment Variables

The script uses the following environment variables, which should be set in a `.env` file (see `example.env`):

- `BHE_DOMAIN`: The domain of the BHE API.
- `BHE_PORT`: The port of the BHE API.
- `BHE_SCHEME`: The scheme of the BHE API (http or https). - BHE_TOKEN_ID: The token ID for the BHE API.
- `BHE_TOKEN_KEY`: The token key for the BHE API.
- `BHE_TOKEN_SECRET`: The token secret for the BHE API.

More details here: [BloodHound API](https://support.bloodhoundenterprise.io/hc/en-us/articles/11311053342619-Working-with-the-BloodHound-API)

## Usage

```bash
python bh-toolset.py [-h] [-i [FILE]] [--new [NEW_FILE]] [--delete]
```

- `-h`: Show the help message and exit.
- `-i`: Import customqueries.json file from legacy format. (default: customqueries.json).
- `--new`: import customqueries already format for the new version. (default: new_customqueries.json).
- `--delete`: Delete all saved queries.

### Example

```bash
# show help
python3 bh-toolset.py -h
# convert and import customqueries from bloodhound legacy
python3 bh-toolset.py -i
# also import already converted customqueries
python3 bh-toolset.py -i --new
# specify custom file names
python3 bh-toolset.py -i my_customqueries.json --new my_new_customqueries.json
# delete all saved queries
python3 bh-toolset.py --delete
```

## Notes

Some attributes like `owner` and `highvalue` have changed in BloodHound Community. You will have to modify those manually (for now). Ex:

- `MATCH (m:User) WHERE m.owned=TRUE RETURN m` is now `MATCH (m:User) WHERE m.system_tags =~ '.*owned*.' RETURN m`
- see more examples in `new_customqueries.json`

## Credits

- [Yack](https://yack.one)
