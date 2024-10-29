Qualtrics.SurveyEngine.addOnload(function () {
	/*Place your JavaScript here to run when the page loads*/

	// Store the embedded data in variables or use random integers if they are empty
	var userID = Qualtrics.SurveyEngine.getEmbeddedData('userID');
	var customSurveyID = Qualtrics.SurveyEngine.getEmbeddedData('customSurveyID');
	var versionID = Qualtrics.SurveyEngine.getEmbeddedData('versionID')
	var questionID =Qualtrics.SurveyEngine.getEmbeddedData('questionID'); // UPDATE THIS FOR EACH QUESTION

    // FIRST QUESTION:
	var first_question = `I am interested in learning more about why you currently do not own any stocks or stock mutual funds. Can you help me understand the main factors or reasons why you are not participating in the stock market?`;

	// TOPIC GUIDE:
	var topics = `{
		"1": "Explore the reasons behind the interviewee's choice to avoid the stock market.",
		"2": "Delve into the perceived barriers or challenges preventing them from participating in the stock market.",
		"3": "Explore a 'what if' scenario where the interviewee invest in the stock market. What would they do? What would it take to thrive? Probing questions should explore the hypothetical scenario.",
		"4": "Prove for conditions or changes needed for the interviewee to consider investing in the stock market."
		}`;
	var topics_length = `[6, 5, 3, 2]`;
	
	var prompt_finish = `{
		"1": "As we conclude our discussion, are there any perspectives or information you feel we haven't addressed that you'd like to share?",
		"2": "Reflecting on our conversation, what would you identify as the main reason you're not participating in the stock market?",
		"3": "Thank you for sharing your insights and experiences today. Your input is invaluable to our research. Please proceed to the next page."
		}`;
	
	// PROMPTS:
	var prompt_topic = `
	CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You're guiding a semi-structured qualitative interview about the interviewee's reasons for not investing in the stock market.

	INPUTS:
	A. Previous Conversation Summary:
	{summary}

	B. Current Conversation:
	{current_topic_history}

	C. Next Interview Topic:
	{next_interview_topic}

	TASK: Introducing the Next Interview Topic from the interview plan by asking a transition question.

	GUIDELINES:
	1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
	2. Natural transition: To make the transition to a new topic feel more natural and less abrupt, you may use elements from the Current Conversation and Previous Conversation Summary to provide context and a bridge from what has been discussed to what will be covered next.
	3. Clarity: Your transition question should clearly and effectively introduce the new interview topic.

	RESPONSE FORMAT: Your response should use the template below:
	'''Question: "Insert your transition question here" '''

	Remember to include "Question:" in your response. Start your response here:`;
	
	var prompt_history = `
	CONTEXT: You're an AI proficient in summarizing qualitative interviews for academic research. You're overseeing the records of a semi-structured qualitative interview about the interviewee's reasons for not investing in the stock market.

	INPUTS:
	A. Interview Plan:
	{topics}

	B. Previous Conversation Summary:
	{summary}

	C. Current Topic:
	{current_topic}

	D. Current Conversation:
	{current_topic_history}

	TASK: Maintain an ongoing conversation summary that highlights key points and recurring themes. The goal is to ensure that future interviewers can continue exploring the reasons for non-participation without having to read the full interview transcripts.

	GUIDELINES:
	1. Relevance: Prioritize and represent information based on their relevance and significance to understanding the interviewee's reasons for not investing in the stock market.
	2. Update the summary: Integrate the Current Conversation into the Previous Conversation Summary, ensuring a coherent and updated overview. Avoid adding redundant information.
	3. Structure: Your summary should follow the interview's chronology, starting with the first topic. Allocate space in the summary based on relevance for the research objective, not just its recency.
	4. Neutrality: Stay true to the interviewee's responses without adding your own interpretations of inferences.
	5. Sensitive topics: Document notable emotional responses or discomfort, so subsequent interviewers are aware of sensitive areas.
	6. Reasons: Keep an up-to-date overview of the interviewee's reasons for non-participation.

	Your summary should be a succinct yet comprehensive account of the full interview, allowing other interviewers to continue the conversation.

	RESPONSE FORMAT: Your response should use the template below:
	'''Summary: "Insert your summary here" '''

	Remember to include "Summary:" in your response. Start your response here:`;

	
	var prompt_probing = `
	CONTEXT: You're an AI proficient in conducting qualitative interviews for academic research. You conduct a qualitative interview with the goal of learning the interviewee's reasons for not investing in the stock market.

	INPUTS:
	A. Previous Conversation Summary:
	{summary}

	B. Current Interview Topic:
	{current_topic}

	C. Current Conversation:
	{current_topic_history}

	TASK: Your task is to formulate the next probing question for the Current Conversation. The question should align with the Current Interview Topic, helping us to better understand and systematically explore why the interviewee is not participating in the stock market.

	GENERAL GUIDELINES:
	1. Open-endedness: Always craft open-ended questions ("how", "what", "why") that allow detailed and authentic responses without limiting the interviewee to  "yes" or "no" answers.
	2. Neutrality: Use questions that are unbiased and don't lead the interviewee towards a particular answer. Don't judge or comment on what was said. It's also crucial not to offer any financial advice.
	3. Respect: Approach sensitive and personal topics with care. If the interviewee signals discomfort, respect their boundaries and move on.
	4. Relevance: Prioritize themes central to the interviewee's stock market non-participation. Don't ask for overly specific examples, details, or experiences that are unlikely to reveal new insights.
	5. Focus: Generally, avoid recaps. However, if revisiting earlier points, provide a concise reference for context. Ensure your probing question targets only one theme or aspect.

	PROBING GUIDELINES:
	1. Depth: Initial responses are often at a "surface" level (brief, generic, or lacking personal reflection). Follow up on promising themes hinting at depth and alignment with the research objective, exploring the interviewee's reasons, motivations, opinions, and beliefs. 
	2. Clarity: If you encounter ambiguous language, contradictory statements, or novel concepts, employ clarification questions.
	3. Flexibility: Follow the interviewee's lead, but gently redirect if needed. Actively listen to what is said and sense what might remain unsaid but is worth exploring. Explore nuances when they emerge; if responses are repetitive or remain on the surface, pivot to areas not yet covered in depth.

	YOUR RESPONSE:`;

	// TEMPERATURES:
	var temperature_probing = 0.7;
	var temperature_topic = 0.7;
	var temperature_history = 0.0;
	var temperature_finish = 0.7;

	// OTHER MODEL PARAMETERS
	var model_name_short = "gpt-4o";
	var model_name_long = "gpt-4o";


    // URL ENDPOINT FOR THE BACKEND API
    var apiEndpoint = "https://lbsnyjijsyk4y5pdiua7ol7uru0fajit.lambda-url.eu-north-1.on.aws/";


	// ID OF FRONT-END ELEMENTS THAT THE CODE INTERACTS WITH
	var inputField = document.getElementById("inputBox");
	var submitButton = document.getElementById("submitButton");
	var chatArea = document.getElementById("chatArea");


	function appendChatbotMessage(message, chatArea, status) {		
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

	// Add the initial question to the chat area
	appendChatbotMessage(first_question, chatArea, "response");

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
			appendChatbotMessage("", chatArea, "waiting");

			// Submit query to backend and wait for the chatbot to reply. Then add the message to the chat area.
			jQuery.ajax({
				url: apiEndpoint,
				// 60 seconds until timeout.
				timeout: 60000,
				type: "POST",
					data: JSON.stringify({
						// The user's response
						message: userMessage,
						// Parameters for the back-end model
						topics: topics,
						topicsLength: topics_length,
						firstQuestion: first_question,
						promptTopic: prompt_topic,
						promptHistory: prompt_history,
						promptFinish: prompt_finish,
						promptProbing: prompt_probing,
						temperatureTopic: temperature_topic,
						temperatureHistory: temperature_history,
						temperatureFinish: temperature_finish,
						temperatureProbing: temperature_probing,
						modelNameShort: model_name_short,
						modelNameLong: model_name_long,
						// Meta data that identifies the user and the conversation.
						userID: userID,
						surveyID: customSurveyID,
						questionID: questionID,
						versionID: versionID
					}),
				contentType: "application/json",
				dataType: "json",
				// REQUEST SUCCESSFUL
				success: function (data) {
					// Extract the 'message' field from the parsedBody
					if (typeof data.body === 'string') {
						try {
							// If it's a string, we'll try to parse it as JSON
							var parsedData = JSON.parse(data.body);
							var chatbotMessage = parsedData.message.trim();
						} catch (error) {
							console.error('Failed to parse the string as JSON:', error);
						}
					} else {
						// If it's not a string, but an object with a "message" property
						var chatbotMessage = data.body.message.trim();
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
						
						// Mark the interview as concluded
						Qualtrics.SurveyEngine.setEmbeddedData('interview_concluded', "1");

					} else {
						// If the string is not present, make the submit button clickable again
						submitButton.disabled = false;
						submitButton.innerText = "Submit response";
						submitButton.style.backgroundColor = '#007BFF';
					}
					// Add the chatbot's message to the chat area
					appendChatbotMessage(chatbotMessage, chatArea, "response");
				},
				// REQUEST UNSUCCESSFUL
				error: function (jqXHR, textStatus, errorThrown) {
					// console.error("Error:", errorThrown);

					error_message_to_user = "Something went wrong... Please try to submit your previous answer again.";
					appendChatbotMessage(error_message_to_user, chatArea, "response");

					// Make the submit button clickable again
					submitButton.disabled = false;
					submitButton.style.backgroundColor = '#007BFF';
					submitButton.innerText = "Submit response";
				}
			});
		}
	});
});

Qualtrics.SurveyEngine.addOnReady(function () {
	/*Place your JavaScript here to run when the page is fully displayed*/

});

Qualtrics.SurveyEngine.addOnUnload(function () {
	/*Place your JavaScript here to run when the page is unloaded*/

});
