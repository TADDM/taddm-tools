# Filename: Notifications.ps1

param (
    [string]$from = "discovery@xxxx.com",
    [string]$to = $(throw "-to is required."),
    [string]$subject = "",
    [string]$body = "",
    [string]$file = ""
)

#SMTP server name
$smtpServer = "smtp.xxxx.com"

function sendMail($from, $to, $subject, $body, $file) {

    Write-Host "Sending Email"

    #Creating a Mail object
    $msg = New-Object Net.Mail.MailMessage

    #Creating SMTP server object
    $smtp = New-Object Net.Mail.SmtpClient($smtpServer)

    #Email structure 
    $msg.From = $from
    #$msg.ReplyTo = "replyto@xxxx.com"
    $msg.To.Add($to)
    $msg.subject = $subject

    $msg.body = ""
    if ($body)
    {
        $message_body = ""
        ForEach ($sInputLine in Get-Content $body)
        {
            $message_body += $sInputLine.Trim() + "`r`n"
        }
        $msg.body = $message_body
    }

    if ($file)
    {
        Write-Host "Adding attachment"
        $attachment = New-Object Net.Mail.Attachment($file, 'Application/Octet')
        $msg.Attachments.Add($attachment)
    }
    
    #Sending email 
    $smtp.Send($msg)
}

#Calling function
sendMail $from $to $subject $body $file