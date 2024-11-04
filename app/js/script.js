var inputField = document.getElementById("user_message");
var submitButton = document.getElementById("submit_button");
var chatArea = document.getElementById("chat_area");
var form = document.querySelector("form");

function appendChatbotMessage(message, status) {		
	// New message from the chatbot
	var messageContent = document.createElement('div');
	messageContent.style.cssText = "word-wrap: break-word; width: 80%; border: 1px solid #F6F6F6; border-radius: 5px; padding: 5px; margin-bottom: 10px; background-color: #F6F6F6; display: block; margin-right: auto;  font-size: 16px;";

	if (status === "waiting") {
		messageContent.innerHTML = createDancingDots();
		messageContent.id = "dancingDots"; // Assign an ID to the waiting message for easier tracking
	} else if (status === "response") {
		var existingDots = document.getElementById("dancingDots");
		if (existingDots) {
			existingDots.innerText = message.trim();
			existingDots.removeAttribute('id');
			chatArea.scrollTop = chatArea.scrollHeight;
			return; // Since the message is replaced, we don't need to append anything new
		} else {
			messageContent.innerText = message.trim();
		}
	}
	// Add label and message to the chat area and scroll to the bottom
	chatArea.appendChild(messageContent);
	chatArea.scrollTop = chatArea.scrollHeight;
}

function createDancingDots() {
	// Create three dancing dots as a placeholder while the user is waiting for a reply.
	return `
    <div word-wrap: break-word; width: 80%; border: 1px solid #F6F6F6; border-radius: 5px; padding: 5px; margin-bottom: 10px; background-color: #F6F6F6; display: block; margin-right: auto;>
		<div id="wave" style="position:relative; vertical-align: center text-align:left"; text-align:center;">
			<span class="dot" style="display:inline-block; width:12px; height:6px; border-radius:50%; margin-right:3px; background:#303131; animation: wave 1.3s linear infinite;"></span>
			<span class="dot" style="display:inline-block; width:12px; height:6px; border-radius:50%; margin-right:3px; background:#303131; animation: wave 1.3s linear infinite; animation-delay: -1.1s;"></span>
			<span class="dot" style="display:inline-block; width:12px; height:6px; border-radius:50%; margin-right:3px; background:#303131; animation: wave 1.3s linear infinite; animation-delay: -0.9s;"></span>
		</div>
		<style>
			@keyframes wave {
				0%, 60%, 100% {
					transform: initial;
				}
				30% {
					transform: translateY(-7px);
				}
			}
		</style>
	</div>`;
}

// Add the initial question to the chat area from Flask message
appendChatbotMessage("{{ data['message'] }}", "response");

// Event listener for the "submit" button
submitButton.addEventListener("click", function () {
	// Get the user response.
	var userMessage = inputField.value.trim();

	// Check if the message was not only white space. Otherwise, do nothing.
	if (userMessage) {
		// Clear the input field
		inputField.value = "";

		// Make the button unclickable until we hear back from chatGPT
		submitButton.disabled = true;
		submitButton.style.backgroundColor = '#ccc';
		submitButton.innerText = "Waiting for reply...";

		var messageContent = document.createElement('div');
		messageContent.style.cssText = "display: inline-block; max-width: 80%; border: 1px solid #ddd; border-radius: 5px; padding: 5px; margin-bottom: 10px; background-color: #ddd; word-wrap: break-word; white-space: pre-wrap; box-sizing: border-box; font-size: 16px; text-align: left;";
		messageContent.innerText = userMessage;
					
		// Add label and message of the user to the chat area and scroll to the bottom
		chatArea.appendChild(messageContent);
		chatArea.scrollTop = chatArea.scrollHeight;

		// Add dancing dots
		appendChatbotMessage("", "waiting");

		// Submit query to backend and wait for the chatbot to reply. Then add the message to the chat area.
		var session_id = "{{ data['session_id'] }}";
		jQuery.ajax({
			url: "{{url_for('next')}}",
			timeout: 60000,
			type: "POST",
			data: JSON.stringify({
				user_message: userMessage,
				session_id: session_id
			}),
			contentType: "application/json",
			dataType: "json",
			// REQUEST SUCCESSFUL
			success: function (data) {
				// Extract the 'message' field from the parsedBody
				if (typeof data === 'string') {
					try {
						// If it's a string, we'll try to parse it as JSON
						var parsedData = JSON.parse(data);
						var chatbotMessage = parsedData.message.trim();
					} catch (error) {
						console.error('Failed to parse the string as JSON:', error);
					}
				} else {
					// If it's not a string, but an object with a "message" property
					var chatbotMessage = data.message.trim();
					console.log("It is property...")
				}

				// Check if this is the last message of the interview
				var endInterviewIndex = chatbotMessage.indexOf("---END---");
				if (endInterviewIndex !== -1) {
					// If it is, remove the string and append the remaining message
					chatbotMessage = chatbotMessage.replace("---END---", "");
					chatbotMessage = chatbotMessage.trim();

					// Make the submit button unclickable and change its text
					submitButton.disabled = true;
					submitButton.innerText = "End of interview";
					
				} else {
					// If the string is not present, make the submit button clickable again
					submitButton.disabled = false;
					submitButton.innerText = "Submit response";
					submitButton.style.backgroundColor = '#007BFF';
				}
				// Add the chatbot's message to the chat area
				appendChatbotMessage(chatbotMessage, "response");
			},
			// REQUEST UNSUCCESSFUL
			error: function (jqXHR, textStatus, errorThrown) {
				// console.error("Error:", errorThrown);

				error_message_to_user = "Something went wrong... Please try to submit your previous answer again.";
				appendChatbotMessage(error_message_to_user, "response");

				// Make the submit button clickable again
				submitButton.disabled = false;
				submitButton.style.backgroundColor = '#007BFF';
				submitButton.innerText = "Submit response";
			}
		});

	}	
});