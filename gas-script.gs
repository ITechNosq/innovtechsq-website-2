function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    // Save to Google Sheet (first sheet)
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    sheet.appendRow([
      new Date(),
      data.name,
      data.phone,
      data.message,
      data.timestamp || new Date().toISOString()
    ]);

    // Send Email Notification
    MailApp.sendEmail({
      to: "pawan.singhsengar26@gmail.com",
      subject: "New Lead from InnovTech Sq Website",
      body: `New form submission:

Name: ${data.name}
Phone: ${data.phone}
Message: ${data.message}
Time: ${data.timestamp || new Date().toISOString()}

---
InnovTech Sq Pvt Ltd`
    });

    return ContentService
      .createTextOutput("Success")
      .setMimeType(ContentService.MimeType.TEXT);
  } catch (error) {
    console.error('Error:', error);
    return ContentService
      .createTextOutput("Error: " + error.toString())
      .setMimeType(ContentService.MimeType.TEXT);
  }
}
