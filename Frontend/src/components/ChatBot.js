import React, { useEffect } from 'react';

const ChatBot = () => {
  useEffect(() => {
    // Ensure the df-messenger is properly initialized
    const messenger = document.querySelector('df-messenger');
    if (messenger) {
      // Any additional configuration can be done here
      console.log('Dialogflow messenger initialized');
    }
  }, []);

  return (
    <df-messenger
      location="us"
      project-id="gen-lang-client-0182599221"
      agent-id="ac7179d3-8135-463a-9593-cdcaa41838e4"
      language-code="en"
      max-query-length="-1"
    >
      <df-messenger-chat-bubble
        chat-title="MedAssureAIAgent"
      >
      </df-messenger-chat-bubble>
    </df-messenger>
  );
};

export default ChatBot;