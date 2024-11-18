import React from "react";
import { useSelector } from "react-redux";
import { Box } from "@mui/material";
import {
    AgentListBar,
    ChatFabGroup,
    ScrollableMessageBox,
    AvatarChatHistory,
    StreamChatBox,
} from "gai-ui";

const DialogueView = () => {
    const selectedPersona = useSelector(
        (state) => state.persona.selectedPersona
    );
    // Set content is triggered by StreamChatBox when text generation is completed
    const setContent = (content) => {
        console.log(content);
    };

    const handleViewMonologue = (agent) => {};
    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                width: "60%",
                paddingLeft: {
                    xs: "0",
                    md: "50px",
                    lg: "50px",
                    xl: "100px",
                },
                paddingRight: {
                    xs: "0",
                    md: "50px",
                    lg: "50px",
                    xl: "100px",
                },
                height: "100%",
                justifyContent: "space-around",
                alignItems: "center",
            }}
        >
            <Box
                style={{
                    position: "absolute",
                    top: "100px",
                    right: "100px",
                    zIndex: 1000, // Higher z-index to float above other content
                }}
            >
                <AgentListBar orientation='vertical' />
            </Box>
            {/* Absolute positioning for FAB */}
            <Box
                style={{
                    position: "absolute",
                    top: "120px",
                    left: "100px",
                    zIndex: 1000, // Higher z-index to float above other content
                }}
            >
                <ChatFabGroup />
            </Box>
            <ScrollableMessageBox>
                <AvatarChatHistory handleViewThoughts={handleViewMonologue} />
            </ScrollableMessageBox>

            {selectedPersona && <StreamChatBox setContent={setContent} />}
            <Box
                sx={{
                    display: "flex",
                    flexDirection: "row",
                    height: "50px",
                }}
            ></Box>
        </Box>
    );
};

export default DialogueView;
