import React, { Component, useState, useEffect } from "react";
import axios from "axios";
import Nav from "./pages/Home/Nav";
import LoginForm from "./pages/Authentication/LoginForm";
import basename from "./pages/Home/basename.js";
import SignupForm from "./pages/Authentication/SignupForm";
import Router from "./pages/Authentication/Router";
import "./App.css";
import { Typography } from "@material-ui/core";


const App = (props) => {
    const [loading, setLoading] = useState(false);
    const [errors, setError] = useState(null);
    const [error1, setError1] = useState(null);
    const [loggedIn, setLoggedIn] = useState(
        localStorage.getItem("token") ? true : false
    );
    const [username, setUsername] = useState("");
    const [userId, setUserId] = useState(0);
    const [user, setUser] = useState({});
    
    // const [is_student,setstudent] =useState("");
    // const [is_trainer,setTeacher] =useState("");

    useEffect(() => {
        if (loggedIn) {
            fetch("https://orolingo-staging.herokuapp.com/auth/current_user/", {
                headers: {
                    Authorization: `JWT ${localStorage.getItem("token")}`,
                },
            })
                .then((res) => res.json())
                .then((json) => {
                    console.log(JSON.stringify(json));
                    setUsername(json.username);
                    setUserId(json.id);
                    setUser(json);
                    console.log(json.id);
                });
        }
    }, [loggedIn]);

    const handleLogin = (e, data, redirect) => {
        setError(null);
        setLoading(true);
        e.preventDefault();
        fetch("https://orolingo-staging.herokuapp.com/token-auth/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        })
            .then((res) => res.json())
            .then((json) => {
                setLoading(false);
                if (json.username && data.username !== json.username) {
                    throw new Error(json.username);
                  }
                  if (json.password && data.password !== json.password) {
                    throw new Error(json.password);
                  }
                  if (json.non_field_errors) {
                    throw new Error(json.non_field_errors[0]);
                  }
                localStorage.setItem("token", json.token);
                setLoggedIn(true);
                setUsername(json.user.username);
                setUserId(json.user.id);
                console.log(json);
                setUser(json.user);

                redirect("/dashboard");
            })
            .catch((error) => {
                setLoading(false);
                console.log(error);
                setError("Incorrect Credentials");
                document.getElementById(
                  "login-form-error"
                ).textContent = error.toString().substring(7);
              });
    };

    const handleSignup = (e, data, redirect) => {
        setError(null);
        setLoading(true);
        e.preventDefault();
        fetch("https://orolingo-staging.herokuapp.com/auth/users/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        })
            .then((res) => res.json())
            .then((json) => {
                setLoading(false);
                console.log(json);
                if (
                    json.username &&
                    json.email &&
                    data.username !== json.username &&
                    data.email !== json.email
                ) {
                    throw new Error(
                        json.username.join("<br />") +
                            "<br />" +
                            json.email.join("<br />")
                    );
                } else if (json.username && data.username !== json.username) {
                    throw new Error(json.username.join("<br />"));
                } else if (json.email && data.email !== json.email) {
                    throw new Error(json.email.join("<br />"));
                }

                if (json.username && data.username !== json.username) {
                    throw new Error(json.username);
                  }
                  if (json.password && data.password !== json.password) {
                    throw new Error(json.password);
                  }
                  if (json.non_field_errors) {
                    throw new Error(json.non_field_errors[0]);
                  }

                localStorage.setItem("token", json.token);
                setLoggedIn(true);
                setUsername(json.username);
                setUserId(json.id);
                console.log(json.username);
                setUser(json); 
                redirect("/dashboard");
            })
            .catch((error) => {
                setLoading(false);
                setError("Something went wrong. Please try again later.");

                setError1("Something went wrong. Please try again later.");
                document.getElementById(
                  "signup-form-error"
                ).textContent = error.toString().substring(7);
            });
    };

    const handleSocialLogin = (response, provider, redirect) => {
        const accessToken = response.accessToken;
        const data = {
            provider: provider,
            access_token: accessToken,
        };
        console.log("social")
        
        fetch("https://orolingo-staging.herokuapp.com/auth/oauth/login/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        })
            .then((res) => res.json())
            .then((json) => {
                if (json.newAccount) {
                    redirect("/account-choice", { json: json });
                } else {
                    localStorage.setItem("token", json.token);
                    setLoggedIn(true);
                    setUsername(json.username);
                    setUserId(json.userId);
                    setUser(json);
                    console.log(json.userId);
                    redirect("/dashboard");
                    console.log(json);
                }
            });
    };

    const handleSocialTrainerStudent = (userData, type, redirect) => {
        console.log(type)
        const data = {
            is_student: type === "Student",
            is_trainer: type === "Trainer",
        };
        if(type == "Student"){                
            axios({
                method: 'get',
                url: `https://orolingo-staging.herokuapp.com/auth/users/${userData.userId}/`,
                headers: {
                    Authorization: `JWT ${userData.token}`,
                    "Content-Type": "application/json",
                },
            })
            .then(res =>{
                axios.post(`${basename}/api/student/`,{
                    'user':res.data,
                    'languages_learnt':[],
                    'languages_to_learn':[]
                })
            })
        }
        else{
            axios({
                method: 'get',
                url: `https://orolingo-staging.herokuapp.com/auth/users/${userData.userId}/`,
                headers: {
                    Authorization: `JWT ${userData.token}`,
                    "Content-Type": "application/json",
                },
            })
            .then(res=>{
                axios.post(`${basename}/api/trainer/`,{
                    'user':res.data
                })
            })
        }
        fetch(`https://orolingo-staging.herokuapp.com/auth/users/${userData.userId}/`, {
            method: "PATCH",
            headers: {
                Authorization: `JWT ${userData.token}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        })
            .then((res) => res.json())
            .then((json) => {
                localStorage.setItem("token", json.token);
                setLoggedIn(true);
                setUsername(json.username);
                setUserId(json.id);
                setUser(json);
                console.log(json);
                
                redirect("/dashboard");
            });
    };

    const handleLogout = () => {
        localStorage.removeItem("token");
        setLoggedIn(false);
        setUsername(username);
        setUser({});
    };

    const getUserDetail = async (userId) => {
        console.log(userId + " from App");
        try {
            const response = await fetch(
                `https://orolingo-staging.herokuapp.com/auth/users/${userId}/`,
                {
                    headers: {
                        Authorization: `JWT ${localStorage.getItem("token")}`,
                    },
                }
            );
            if (response.ok) {
                const jsonResponse = await response.json();
                console.log("success");
                console.log(jsonResponse);
                return jsonResponse;
            }
            throw new Error("Request Failed!");
        } catch (error) {
            console.log(error);
        }
    };

    return (
        <Router
            loggedIn={loggedIn}
            username={username}
            userId={userId}
            user={user}
            errors={errors}
            error1={error1}
            getUserDetail={getUserDetail}
            handleLogin={handleLogin}
            handleSignup={handleSignup}
            handleLogout={handleLogout}
            handleSocialLogin={handleSocialLogin}
            handleSocialTrainerStudent={handleSocialTrainerStudent}
        />
    );
};

export default App;
