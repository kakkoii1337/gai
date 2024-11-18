import React, { useEffect, useState } from "react";
import { Backdrop, Button } from "@mui/material";
import { themes, GeneralTab, useGeneralTab } from "gai-ui";

const ProvisionView = () => {
    const theme = themes(true);
    const { deletePersonaAsync, savePersonaAsync, myPersona } = useGeneralTab();
    const [open, setOpen] = useState(true);
    const [refresh, setRefresh] = useState(true);
    const handleSave = async () => {
        await savePersonaAsync();
        setOpen(false);
        console.log("Save");
    };
    const handleDelete = async () => {
        await deletePersonaAsync();
        setRefresh(true);
    };
    const isReady = myPersona?.AgentDescription;
    return (
        <Backdrop
            open={open}
            style={{
                zIndex: theme.zIndex.drawer + 1,
                color: "#fff",
                backgroundColor: "rgba(0, 0, 0, 0.6)",
                transition: "opacity 0.5s ease-in-out",
            }}
            onClick={(e) => e.stopPropagation()}
        >
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "start",
                    minHeight: "700px",
                    minWidth: "1000px",
                    maxHeight: "700px",
                    maxWidth: "1000px",
                }}
            >
                <div
                    style={{
                        display: "flex",
                        height: "80px",
                    }}
                >
                    <h1
                        style={{
                            color: theme.palette.text.secondary,
                        }}
                    >
                        Agent Configuration
                    </h1>
                </div>
                <div
                    style={{
                        display: "flex",
                        height: "500px",
                        width: "1000px",
                        flexDirection: "row",
                        backgroundColor: theme.palette.background.paper,
                        borderRadius: "10px",
                        margin: 0,
                        padding: "10px",
                        justifyContent: "space-around",
                        gap: "5px",

                        borderBottom: 1,
                        borderColor: "gray",
                        flexGrow: 1,
                    }}
                >
                    <GeneralTab refresh={refresh} setRefresh={setRefresh} />
                </div>
                <div
                    style={{
                        display: "flex",
                        flexDirection: "row",
                        width: "100%",
                        justifyContent: "center",
                        height: "40px",
                        marginTop: "20px",
                        marginBottom: "20px",
                        gap: "20px",
                    }}
                >
                    <Button
                        variant='contained'
                        color='primary'
                        disabled={
                            //myPersona === null
                            false
                        }
                        sx={{
                            borderRadius: "10px",
                            color: theme.palette.text.primary,
                            backgroundColor: theme.palette.background.default,
                            "&.Mui-disabled": {
                                backgroundColor:
                                    theme.palette.background.default,
                            },
                            display: isReady ? "block" : "none",
                        }}
                        onClick={handleDelete}
                    >
                        Delete
                    </Button>
                    <Button
                        variant='contained'
                        sx={{
                            borderRadius: "10px",
                            color: theme.palette.text.primary,
                            backgroundColor: theme.palette.background.default,
                            display: isReady ? "block" : "none",
                        }}
                        onClick={handleSave}
                    >
                        Save
                    </Button>
                </div>
            </div>
        </Backdrop>
    );
};

export default ProvisionView;
