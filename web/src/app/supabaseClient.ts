import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = "https://kybwqugpfsfzkyuhngwv.supabase.co"
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt5YndxdWdwZnNmemt5dWhuZ3d2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc2MzEyNjAsImV4cCI6MjA2MzIwNzI2MH0.oDJ04R3CZmcuPPmFYIb_8t1Rz5MkK0Ji8Wl1Ur40yEw"

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);