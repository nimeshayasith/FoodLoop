const env = import.meta.env;
export const API_URL = (env.VITE_API_URL || "").replace(/\/$/, "");
export const REGION = env.VITE_REGION || "ap-south-1";
export const CLIENT_ID = env.VITE_USER_POOL_CLIENT_ID || "";
export const IMAGE_BASE_URL = (env.VITE_IMAGE_BASE_URL || "").replace(/\/$/, "");

export const DISTRICTS = ["Ampara","Anuradhapura","Badulla","Batticaloa","Colombo","Galle","Gampaha","Hambantota","Jaffna","Kalutara","Kandy","Kegalle","Kilinochchi","Kurunegala","Mannar","Matale","Matara","Monaragala","Mullaitivu","Nuwara Eliya","Polonnaruwa","Puttalam","Ratnapura","Trincomalee","Vavuniya"];
export const CATEGORIES = ["Bakery","Cooked meals","Fruits & vegetables","Dairy","Groceries","Beverages","Other"];
export const BUSINESS_TYPES = ["Supermarket","Bakery","Restaurant","Hotel","Food producer","Other"];
export const CATEGORY_EMOJI = { "Bakery":"🍞","Cooked meals":"🍛","Fruits & vegetables":"🥭","Dairy":"🥛","Groceries":"🛒","Beverages":"🧃","Other":"🍽️" };
