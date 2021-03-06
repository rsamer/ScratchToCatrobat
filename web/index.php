<?php
function valueForConfigKey($key, $rawConfigContent) {
	$start = strpos($rawConfigContent, $key);
	$temp = substr($rawConfigContent, $start);
	$end = strpos($temp, "\n");
	$start = strlen($key);
	$end = $end - $start;
	return trim(substr($temp, $start, $end));
}

$rawConfigContent = file_get_contents('../config/default.ini');
$versionNumber = valueForConfigKey('version:', $rawConfigContent);
$buildName = valueForConfigKey('build_name:', $rawConfigContent);
$buildNumber = valueForConfigKey('build_number:', $rawConfigContent);
?><!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
  <meta name="robots" content="noindex,nofollow"/>
  <meta name="viewport" content="width=device-width">
  <title>Scratch to Catrobat Converter</title>
  <link rel="stylesheet" href="./css/bootstrap.min.css">
  <link rel="stylesheet" href="./css/bootstrap-theme.min.css">
  <script src="./js/bootstrap.min.js"></script>
  <link rel="shortcut icon" href="./images/logo/favicon.png" />
  <link rel="stylesheet" href="./css/main.css" media="screen"/>
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script>
  <script>
    jQuery(document).ready(function($) {
		$("#btn-convert").removeClass("deactivate-button").addClass("activate-button");
		$("#version-link").click(function() {
			alert("Build: <?php echo $buildName; ?>, <?php echo $buildNumber; ?>");
			return false;
		})
		$("#field-url").blur(function() {
			var projectURL = $(this).val();
			var urlParts = projectURL.split("/");
			$("#field-url-validation-result").html("");
			if (urlParts.length < 5) {
				$("#field-url-validation-result").append($("<div></div>").text("Invalid URL given!").css("color", "#FF0000").css("font-weight", "bold"));
				$("#btn-convert").removeClass("deactivate-button").removeClass("activate-button").addClass("deactivate-button");
				$(this).focus();
				return;
			}
			var projectID = urlParts[urlParts.length - 1];
			if (projectID == "") {
				projectID = urlParts[urlParts.length - 2];
			}
			var projectMetadataURL = "https://scratch.mit.edu/api/v1/project/" + projectID + "/?format=json";
			$.getJSON(projectMetadataURL, function(data) {
				var div = $("<div></div>").html("<b>Title of project:</b> " + data["title"]);
				var projectMetadataDiv = $("<div></div>").append(div);
				$("#field-url-validation-result").append(projectMetadataDiv);
			});
			$("#btn-convert").removeClass("deactivate-button").removeClass("activate-button").addClass("activate-button");
		});
    });
  </script>
</head>
<body>
  <div class="ribbon">
    <a href="#" id="version-link">version <?php echo $versionNumber; ?></a>
  </div>
  <div id="wrapper">
    <header>
      <nav>
        <div id="header-top">
          <div><a href="https://share.catrob.at/pocketcode/help">Tutorials</a></div>
          <div><a href="http://www.catrobat.org">About</a></div>
        </div>

        <div id="header-left">
          <div id="logo">
            <a href="/pocketcode/">
              <img src="/images/logo/logo_text.png" alt="Pocket Code Logo" />
            </a>
          </div>
        </div>
      </nav>
    </header>

    <article>
      <div id="featuredPrograms">
		<p>&nbsp;</p>
		<div>
	        <h2>Convert Scratch projects to Catrobat</h2>
            <p>Quickly turn your Scratch desktop projects into full-fledged mobile Catrobat projects</p>
			<p>&nbsp;</p>
            <form action="convert.php" method="post" enctype="multipart/form-data">
				<p style="font-size:18px;">Enter a Scratch project URL ...</p>
				<div class="input-field">
					<input type="text" id="field-url" name="url" value="http://scratch.mit.edu/projects/10205819/" class="clearable" />
				</div>
				<div id="field-url-validation-result"></div>
			<div class="separator-line"></div>
            <p style="font-size:18px;">... or upload a Scratch project ...</p>
			<div class="input-field">
              <input type="file" id="field-filename" name="filename" class="size-large input-search" />
            </div>
			<div class="separator-line"></div>
			<input type="submit" name="submit" id="btn-convert" value="Convert" class="convert-button deactivate-button" />
	        </form>
		</div>
		<div class="separator-line big-margin"></div>
		<div>
          <h2>How it works</h2>
          <div>
            <ul>
              <li>Select your Scratch project of choice or enter the project URL in the input field above and hit the "Convert" button.</li>
              <li>After the conversion has finished a QR-Code will be shown.</li>
              <li>Install and open the PocketCode app on your <a href="https://play.google.com/store/apps/details?id=org.catrobat.catroid" target="_blank">Android</a> or iOS device (coming soon).</li>
              <li>Now hold your device over the QR Code so that it's clearly visible within your smartphone's screen.</li>
              <li>Your project should subsequently open on your mobile device.</li>
			  <li>Have fun! :)</li>
            </ul>
          </div>
		</div>
      </div>
    </article>
  </div>
  <p>&nbsp;</p>
  <footer>
    <div id="footer-menu" class="footer-padding">
      <div>&copy; Copyright 2014 - 2015 Catrobat Team</div>
    </div>
  </footer>
  <p>&nbsp;</p>
  <p>&nbsp;</p>
</body>
</html>
