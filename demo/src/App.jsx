import React, {useState,useEffect} from "react";
import { Provider } from "react-redux";

// MUI
import { ThemeProvider } from "@mui/material/styles";
import { CssBaseline, Box } from "@mui/material";

// lib
import { store, themes, NavbarWrapper, MainBox, httpGetAsync } from "gai-ui";
import DialogueView from "./dialogue/DialogueView";
import ProvisionView from "./persona/ProvisionView";

const isProvisioned = async () => {
    const personaId = "00000000-0000-0000-0000-000000000000";
    const url = `http://localhost:12033/api/v1/persona/profile/${personaId}`;
    try {
        const response = await httpGetAsync(url, null);
        if (response.status === 200) {
            let data = await response.json();
            return data != null;
        } else {
            console.error(`Error: ${response.status}`);
        }
    } catch (error) {
        console.error("Failed to fetch:", error);
    }
};

const ViewSelector = () => {
    const [currentView, setCurrentView] = useState(false);

    useEffect(() => {
        const check = async () => {
            const provisioned = await isProvisioned();
            if (!provisioned) {
                setCurrentView("provision");
            }
            setCurrentView("dialogue");
        };
        check();
    }, []);

    return (
        <Box
            sx={{
                width: "100%",
                height: "100%",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
            }}
        >
            <ProvisionView
                sx={{
                    position: "absolute",
                    visibility:
                        currentView === "provision" ? "visible" : "hidden",
                    opacity: currentView === "provision" ? "1" : "0",
                    transition: "opacity 0.5s ease-in-out",
                }}
            />
            <DialogueView
                sx={{
                    position: "absolute",
                    visibility:
                        currentView === "dialogue" ? "visible" : "hidden",
                    opacity: currentView === "dialogue" ? "1" : "0",
                    transition: "opacity 0.5s ease-in-out",
                }}
            />
        </Box>
    );
};

const App = () => {
    return (
        <ThemeProvider theme={themes(true)}>
            <CssBaseline />
            <NavbarWrapper>
                <MainBox>
                    <ViewSelector />
                </MainBox>
            </NavbarWrapper>
        </ThemeProvider>
    );
};

const ReduxApp = () => (
    <Provider store={store}>
        <App />
    </Provider>
);

export default ReduxApp;
