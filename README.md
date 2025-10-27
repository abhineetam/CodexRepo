# Network Printer Web App

This project provides a simple Flask-based web interface that allows a user to
submit a document, PDF, or image to a network printer. The user specifies the
printer's address (an IP address or protocol URI) and uploads the file to be
printed. The server then dispatches the print job using either IPP (via the
`lp` command) or a raw socket connection on port 9100 for printers that support
JetDirect/RAW printing.

## Features

- Upload common document and image formats up to 64&nbsp;MB per file.
- Accepts printer addresses as plain IPs (auto-converted to IPP) or as
  `ipp://`, `ipps://`, `lpd://`, or `socket://` URIs.
- Uses the system `lp` command when available for IPP/LPR printing.
- Falls back to direct socket streaming for printers that expose a RAW port.
- Provides user-friendly feedback via the web interface.

## Requirements

- Python 3.10+
- Flask
- A POSIX environment with the `lp` command available for IPP printing
  (installable via CUPS packages). If `lp` is unavailable, only RAW socket
  printing will work.

Install the Python dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the App

Start the Flask development server:

```bash
flask --app app run --debug
```

By default, the application listens on `http://127.0.0.1:5000/`.

## Usage Notes

1. Enter the printer's address in one of the supported formats.
   - Example IPP printer: `ipp://192.168.1.25/ipp/print`
   - Example RAW socket printer: `socket://192.168.1.50:9100`
   - Providing only an IP address assumes IPP on `/ipp/print`.
2. Choose a file to upload and submit the form.
3. Review the status message displayed after submission.

## Security Considerations

- Only enable this interface on trusted networks; the app does not implement
  authentication or authorization.
- Uploaded files are stored temporarily in the system temp directory and
  removed immediately after being sent to the printer.
