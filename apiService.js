import axios from "axios";

const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'; // Load from .env

// Generic GET request
export const getRequest = async (endpoint, params = {}) => {
    try {
        const response = await axios.get(`${apiBaseUrl}${endpoint}`, {
            params,
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "accept": "text/html"
            },
        });
        return response.data;
    } catch (error) {
        console.error(`GET ${endpoint} failed:`, error);
        throw error;
    }
};
// Generic POST request
export const registerUser = async (formData) => {
  const response = await fetch('http://localhost:8000/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(formData),
    credentials: 'include', // To send cookies if needed
  });
  
  if (!response.ok) {
    throw new Error('Signup failed');
  }
  return await response.json();
};


export const loginUser = async (formData) => {
  const formParams = new URLSearchParams();
  formParams.append("email", formData.email);
  formParams.append("password", formData.password);
 
  try {
    const response = await fetch("http://localhost:8000/login", {
      method: 'POST',
      headers: {
        "Content-Type": 'application/x-www-form-urlencoded',
      },
      body: formParams,
    });
   
    if (!response.ok) {
      throw new Error("Login Failed");
    }
   
    const data = await response.json();
   
    // Store the JWT token in localStorage
    localStorage.setItem("token", data.access_token);
   
    return data;
  } catch (error) {
    console.error(error);
    throw error;
  }
};

export const isLoggedIn = () => {
  const token = localStorage.getItem("token");
  return !!token;  // Returns true if token exists
};

export const createEvent = async (formData) => {
  const formParams = new URLSearchParams();
  formParams.append("event_name", formData.eventName);
  formParams.append("venue_address", formData.eventVenue);
  formParams.append("event_date", formData.startDate);
  formParams.append("audience", formData.audience ? 'true' : 'false');
  formParams.append("delegates", formData.delegates ? 'true' : 'false');
  formParams.append("speaker", formData.speaker ? 'true' : 'false');
  formParams.append("nri", formData.nri ? 'true' : 'false');

  const token = localStorage.getItem("token");

  try {
    const response = await fetch("http://localhost:8000/create_event", {
      method: 'POST',
      headers: {
        "Content-Type": 'application/x-www-form-urlencoded',
        "Authorization": `Bearer ${token}`  // Include the token here
      },
      body: formParams,
      credentials: 'include', // Include this if your backend expects cookies
    });

    if (!response.ok) {
      throw new Error("Event creation failed");
    }

    return await response.json();
  } catch (error) {
    console.error(error);
    throw error;
  }
};

export const eventsave = async (formData) => {
  const formParams = new URLSearchParams();
  formParams.append("event_name", formData.event_name);
  formParams.append("venue_address", formData.venue_address);
  formParams.append("event_date", formData.event_date);

  // Append individual boolean values
  formParams.append("audience", formData.audience ? 'true' : 'false');
  formParams.append("delegates", formData.delegates ? 'true' : 'false');
  formParams.append("speaker", formData.speaker ? 'true' : 'false');
  formParams.append("nri", formData.nri ? 'true' : 'false');

  const token = localStorage.getItem("token"); // Retrieve the token from localStorage

  try {
    const response = await axios.post("http://localhost:8000/create_event", formParams, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": `Bearer ${token}`, // Include the token in the request
      },
      withCredentials: true, // Include if you need to send credentials (e.g., cookies)
    });
    return response.data;
  } catch (error) {
    console.error("Error creating event:", error);
    throw error;
  }
};


 
// Generic PUT request
export const putRequest = async (endpoint, data = {}) => {
    try {
        const response = await axios.put(`${apiBaseUrl}${endpoint}`, data, {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "accept": "text/html"
            },
        });
        return response.data;
    } catch (error) {
        console.error(`PUT ${endpoint} failed:`, error);
        throw error;
    }
};

// Generic DELETE request
export const deleteRequest = async (endpoint) => {
    try {
        const response = await axios.delete(`${apiBaseUrl}${endpoint}`, {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "accept": "text/html"
            },
        });
        return response.data;
    } catch (error) {
        console.error(`DELETE ${endpoint} failed:`, error);
        throw error;
    }
};
