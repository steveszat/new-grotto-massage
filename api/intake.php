<?php
// public_html/api/intake.php
// Handles POST from your intake.html <form action="/api/intake" method="post">
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
  http_response_code(405);
  echo json_encode(['error' => 'Method Not Allowed']);
  exit;
}

$config = require __DIR__ . '/config.php';

// Basic anti-bot honeypot (add a hidden input named "company" in the form if you want)
// If set and non-empty, reject silently
if (!empty($_POST['company'] ?? '')) {
  http_response_code(200);
  echo json_encode(['ok' => true]); // pretend success
  exit;
}

// Helpers
function cuid(): string {
  $data = random_bytes(9);
  return bin2hex($data); // 18 hex chars; we’ll left-pad to 24 for uniformity
}
function normBool($v): int {
  return (isset($v) && ($v === 'yes' || $v === 'on' || $v === '1' || $v === 1 || $v === true)) ? 1 : 0;
}
function arr($key): array {
  return isset($_POST[$key]) ? (array)$_POST[$key] : [];
}
function str($key, $max=1000): ?string {
  if (!isset($_POST[$key])) return null;
  $v = trim((string)$_POST[$key]);
  return $v === '' ? null : mb_substr($v, 0, $max);
}

try {
  // Required fields (as per your client-side checks)
  $name    = str('name', 200);
  $sigName = str('sigName', 200);
  $consent = normBool($_POST['consent'] ?? null);

  if (!$name || !$sigName || !$consent) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required signature consent and/or name']);
    exit;
  }

  // Map fields
  $intakeDate  = str('intakeDate', 30);
  $address     = str('address', 255);
  $phone       = str('phone', 40);
  $email       = str('email', 255);
  $under17     = normBool($_POST['under17'] ?? null);

  $health          = arr('health');
  $pregnant        = in_array('Currently Pregnant', $health, true) ? 1 : 0; // matches your checkbox value
  $dueDate         = str('dueDate', 30);
  $healthNotes     = str('healthNotes', 5000);
  $medAware        = str('medAware', 3) ?? 'No';
  $medAwareExplain = str('medAwareExplain', 5000);
  $medications     = str('medications', 5000);

  $massageType = arr('massageType');
  $painAreas   = str('painAreas', 5000);
  $avoidAreas  = str('avoidAreas', 5000);
  $partsMassaged = str('partsMassaged', 5000);

  $contactTxn = arr('contact_txn'); // ["Text","Phone","Email"] possible
  $contactTxnText  = in_array('Text',  $contactTxn, true) ? 1 : 0;
  $contactTxnCall  = in_array('Phone', $contactTxn, true) ? 1 : 0;
  $contactTxnEmail = in_array('Email', $contactTxn, true) ? 1 : 0;

  $mktOptIn = normBool($_POST['mktOptIn'] ?? null);

  $sigDate      = str('sigDate', 30);
  $isoTimestamp = str('isoTimestamp', 40);

  // Page version (optional). If you add <meta name="intake-version" content="...">, submit it as hidden input.
  $pageVersion = str('pageVersion', 64);

  // Server metadata
  $ip  = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? null;
  if ($ip && strpos($ip, ',') !== false) { $ip = trim(explode(',', $ip)[0]); }
  $ua  = $_SERVER['HTTP_USER_AGENT'] ?? null;

  // Evidence digest (hash of disclosure + signed name + timestamps)
  $canonical = json_encode([
    'disclosure'    => $config['disclosure_text'],
    'sig_name'      => $sigName,
    'sig_date'      => $sigDate,
    'iso_timestamp' => $isoTimestamp
  ], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
  $evidenceDigest = hash('sha256', $canonical);

  // Prepare DB
  $dsn = sprintf('mysql:host=%s;dbname=%s;charset=utf8mb4', $config['db_host'], $config['db_name']);
  $pdo = new PDO($dsn, $config['db_user'], $config['db_pass'], [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
  ]);

  $stmt = $pdo->prepare("
    INSERT INTO intakes (
      id, created_at, name, intake_date, address, phone, email, under17,
      health, pregnant, due_date, health_notes, med_aware, med_aware_explain, medications,
      massage_type, pain_areas, avoid_areas, parts_massaged,
      contact_txn_text, contact_txn_call, contact_txn_email, mkt_opt_in,
      consent, sig_name, sig_date, iso_timestamp, ip, user_agent, page_version, evidence_digest
    ) VALUES (
      :id, NOW(), :name, :intake_date, :address, :phone, :email, :under17,
      :health, :pregnant, :due_date, :health_notes, :med_aware, :med_aware_explain, :medications,
      :massage_type, :pain_areas, :avoid_areas, :parts_massaged,
      :contact_txn_text, :contact_txn_call, :contact_txn_email, :mkt_opt_in,
      :consent, :sig_name, :sig_date, :iso_timestamp, :ip, :user_agent, :page_version, :evidence_digest
    )
  ");

  $id = str_pad(cuid(), 24, '0', STR_PAD_LEFT);

  $stmt->execute([
    ':id' => $id,
    ':name' => $name,
    ':intake_date' => date('Y-m-d', strtotime($intakeDate ?? 'today')),
    ':address' => $address,
    ':phone' => $phone,
    ':email' => $email,
    ':under17' => $under17,

    ':health' => $health ? json_encode(array_values($health), JSON_UNESCAPED_UNICODE) : null,
    ':pregnant' => $pregnant,
    ':due_date' => $dueDate ? date('Y-m-d', strtotime($dueDate)) : null,
    ':health_notes' => $healthNotes,
    ':med_aware' => ($medAware === 'Yes' ? 'Yes' : 'No'),
    ':med_aware_explain' => $medAwareExplain,
    ':medications' => $medications,

    ':massage_type' => $massageType ? json_encode(array_values($massageType), JSON_UNESCAPED_UNICODE) : null,
    ':pain_areas' => $painAreas,
    ':avoid_areas' => $avoidAreas,
    ':parts_massaged' => $partsMassaged,

    ':contact_txn_text' => $contactTxnText,
    ':contact_txn_call' => $contactTxnCall,
    ':contact_txn_email' => $contactTxnEmail,

    ':mkt_opt_in' => $mktOptIn,

    ':consent' => $consent,
    ':sig_name' => $sigName,
    ':sig_date' => date('Y-m-d', strtotime($sigDate ?? 'today')),
    ':iso_timestamp' => date('Y-m-d H:i:s', strtotime($isoTimestamp ?? 'now')),
    ':ip' => $ip,
    ':user_agent' => $ua,
    ':page_version' => $pageVersion,
    ':evidence_digest' => $evidenceDigest
  ]);

  // OPTIONAL: send a simple JSON response the frontend can use to redirect
  echo json_encode(['ok' => true, 'id' => $id]);

} catch (Throwable $e) {
  http_response_code(500);
  echo json_encode(['error' => 'Server error', 'detail' => $e->getMessage()]);
}
