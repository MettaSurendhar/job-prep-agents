param(
    [string]$Message = "Your daily job prep is ready!"
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Job Prep Agents"
$form.Size = New-Object System.Drawing.Size(420, 220)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MinimizeBox = $true
$form.MaximizeBox = $false
$form.TopMost = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(15, 17, 21)

$label = New-Object System.Windows.Forms.Label
$label.Text = $Message
$label.AutoSize = $false
$label.Size = New-Object System.Drawing.Size(370, 120)
$label.Location = New-Object System.Drawing.Point(20, 20)
$label.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$label.ForeColor = [System.Drawing.Color]::FromArgb(230, 232, 235)
$form.Controls.Add($label)

$button = New-Object System.Windows.Forms.Button
$button.Text = "OK"
$button.Size = New-Object System.Drawing.Size(90, 32)
$button.Location = New-Object System.Drawing.Point(300, 145)
$button.BackColor = [System.Drawing.Color]::FromArgb(94, 179, 255)
$button.ForeColor = [System.Drawing.Color]::White
$button.FlatStyle = "Flat"
$button.Add_Click({ $form.Close() })
$form.Controls.Add($button)
$form.AcceptButton = $button

$form.Add_Shown({ $form.Activate() })
[void]$form.ShowDialog()
