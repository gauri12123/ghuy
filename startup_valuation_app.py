import streamlit as st
import google.generativeai as genai
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd
import re

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBcUTKcazuwRRqCwy0YuHvHIVE2cFcQ1KI"
genai.configure(api_key="AIzaSyAljEi_5PGC8BGjCvT9aULkVb6xh1mgj_Q")

# Page configuration
st.set_page_config(
    page_title="AI Startup Valuation Estimator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main-header {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
        font-size: 2.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .login-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        max-width: 400px;
        margin: 2rem auto;
    }
    
    .valuation-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .success-alert {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #e3f2fd;
        color: #0d47a1;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #2196F3;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: bold;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #45a049, #4CAF50);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 2px solid #ddd;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4CAF50;
        box-shadow: 0 0 0 0.2rem rgba(76,175,80,0.25);
    }
    
    .stSelectbox > div > div > select {
        border-radius: 6px;
        border: 2px solid #ddd;
    }
    
    .sidebar .stButton > button {
        background: linear-gradient(90deg, #ff6b6b, #ee5a24);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'valuation_history' not in st.session_state:
    st.session_state.valuation_history = []

# Mock user database (in production, use proper database)
USERS = {
    "admin": "admin123",
    "investor": "invest2024",
    "analyst": "analyst123",
    "demo": "demo"
}

def authenticate_user(username, password):
    """Authenticate user credentials"""
    return USERS.get(username) == password

def login_page():
    """Display login page"""
    st.markdown('<div class="main-header"><h1>🚀 AI Startup Valuation Estimator</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("### 🔐 Login to Continue")
        
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Login"):
                if authenticate_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials!")
        
        with col_btn2:
            if st.button("Demo Login"):
                st.session_state.logged_in = True
                st.session_state.username = "demo"
                st.success("Demo login successful!")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Demo credentials info
        st.markdown("""
        <div class="info-box">
            <strong>Demo Credentials:</strong><br>
            Username: demo | Password: demo<br>
            Username: admin | Password: admin123
        </div>
        """, unsafe_allow_html=True)

def get_valuation_prompt(company_data):
    """Generate comprehensive prompt for Gemini API"""
    prompt = f"""
    You are an expert startup valuation analyst. Please provide a comprehensive valuation analysis for the following startup:

    Company Details:
    - Company Name: {company_data['name']}
    - Industry: {company_data['industry']}
    - Stage: {company_data['stage']}
    - Revenue (Annual): ${company_data['revenue']:,}
    - Growth Rate: {company_data['growth_rate']}%
    - Team Size: {company_data['team_size']}
    - Funding Raised: ${company_data['funding_raised']:,}
    - Market Size: ${company_data['market_size']:,}
    - Business Model: {company_data['business_model']}
    - Competitive Advantage: {company_data['competitive_advantage']}

    Please provide:
    1. Estimated valuation range (low, medium, high)
    2. Key valuation drivers and risks
    3. Comparison with industry benchmarks
    4. Recommendations for value enhancement
    5. Investment attractiveness score (1-10)

    Format your response as a structured analysis with clear sections.
    """
    return prompt

def get_ai_valuation(company_data):
    """Get AI-powered valuation analysis"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = get_valuation_prompt(company_data)
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating valuation: {str(e)}"

def extract_valuation_numbers(ai_response):
    """Extract numerical values from AI response"""
    try:
        # Look for valuation ranges in the response
        numbers = re.findall(r'\$?([\d,]+(?:\.\d+)?)[MmBb]?', ai_response)
        if numbers:
            # Convert to float and take meaningful values
            vals = []
            for num in numbers:
                clean_num = float(num.replace(',', ''))
                if clean_num > 1000:  # Likely a valuation number
                    vals.append(clean_num)
            
            if vals:
                return {
                    'low': min(vals) * 0.8,
                    'medium': sum(vals) / len(vals),
                    'high': max(vals) * 1.2
                }
    except:
        pass
    
    # Fallback calculation based on revenue and growth
    return {
        'low': st.session_state.form_data['revenue'] * 2,
        'medium': st.session_state.form_data['revenue'] * 5,
        'high': st.session_state.form_data['revenue'] * 10
    }

def create_valuation_chart(valuations):
    """Create interactive valuation chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=['Low Estimate', 'Medium Estimate', 'High Estimate'],
        y=[valuations['low'], valuations['medium'], valuations['high']],
        marker_color=['#ff6b6b', '#4CAF50', '#2196F3'],
        text=[f'${val:,.0f}' for val in valuations.values()],
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Startup Valuation Estimates',
        xaxis_title='Estimate Type',
        yaxis_title='Valuation ($)',
        template='plotly_white',
        height=400
    )
    
    return fig

def main_app():
    """Main application interface"""
    # Header
    st.markdown('<div class="main-header"><h1>🚀 AI Startup Valuation Estimator</h1></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}! 👋")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        st.markdown(f"**Valuations Created:** {len(st.session_state.valuation_history)}")
        st.markdown(f"**Session Time:** {datetime.now().strftime('%H:%M:%S')}")
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="valuation-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Company Information")
        
        # Company input form
        company_name = st.text_input("Company Name", placeholder="e.g., TechStartup Inc.")
        
        col_industry, col_stage = st.columns(2)
        with col_industry:
            industry = st.selectbox("Industry", [
                "Technology", "Healthcare", "Finance", "E-commerce", 
                "SaaS", "Biotech", "FinTech", "EdTech", "Other"
            ])
        
        with col_stage:
            stage = st.selectbox("Funding Stage", [
                "Pre-seed", "Seed", "Series A", "Series B", 
                "Series C", "Later Stage", "Pre-IPO"
            ])
        
        col_rev, col_growth = st.columns(2)
        with col_rev:
            revenue = st.number_input("Annual Revenue ($)", min_value=0, value=100000)
        
        with col_growth:
            growth_rate = st.number_input("Growth Rate (%)", min_value=0, max_value=1000, value=50)
        
        col_team, col_funding = st.columns(2)
        with col_team:
            team_size = st.number_input("Team Size", min_value=1, value=10)
        
        with col_funding:
            funding_raised = st.number_input("Funding Raised ($)", min_value=0, value=500000)
        
        market_size = st.number_input("Total Market Size ($)", min_value=0, value=1000000000)
        
        business_model = st.selectbox("Business Model", [
            "B2B SaaS", "B2C App", "Marketplace", "E-commerce", 
            "Subscription", "Freemium", "Enterprise", "Other"
        ])
        
        competitive_advantage = st.text_area("Competitive Advantage", 
                                           placeholder="Describe key differentiators...")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Submit button
        if st.button("🔍 Get AI Valuation Analysis"):
            if company_name and competitive_advantage:
                # Store form data
                st.session_state.form_data = {
                    'name': company_name,
                    'industry': industry,
                    'stage': stage,
                    'revenue': revenue,
                    'growth_rate': growth_rate,
                    'team_size': team_size,
                    'funding_raised': funding_raised,
                    'market_size': market_size,
                    'business_model': business_model,
                    'competitive_advantage': competitive_advantage
                }
                
                with st.spinner("🤖 AI is analyzing your startup..."):
                    ai_response = get_ai_valuation(st.session_state.form_data)
                    st.session_state.ai_response = ai_response
                    
                    # Add to history
                    st.session_state.valuation_history.append({
                        'timestamp': datetime.now(),
                        'company': company_name,
                        'valuation': ai_response[:200] + "..."
                    })
                
                st.success("Analysis complete! Check the results →")
            else:
                st.error("Please fill in all required fields!")
    
    with col2:
        st.markdown('<div class="valuation-card">', unsafe_allow_html=True)
        st.markdown("### 📈 Valuation Analysis")
        
        if 'ai_response' in st.session_state:
            # Extract and display valuation numbers
            valuations = extract_valuation_numbers(st.session_state.ai_response)
            
            # Display metrics
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            
            with col_metric1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>${valuations['low']:,.0f}</h3>
                    <p>Low Estimate</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_metric2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>${valuations['medium']:,.0f}</h3>
                    <p>Medium Estimate</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_metric3:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>${valuations['high']:,.0f}</h3>
                    <p>High Estimate</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Valuation chart
            fig = create_valuation_chart(valuations)
            st.plotly_chart(fig, use_container_width=True)
            
            # AI Analysis
            st.markdown("### 🤖 AI Analysis Report")
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.ai_response)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Download report
            if st.button("📥 Download Report"):
                report_data = {
                    'company': st.session_state.form_data['name'],
                    'analysis': st.session_state.ai_response,
                    'valuations': valuations,
                    'timestamp': datetime.now().isoformat()
                }
                
                st.download_button(
                    label="Download JSON Report",
                    data=json.dumps(report_data, indent=2),
                    file_name=f"{st.session_state.form_data['name']}_valuation_report.json",
                    mime="application/json"
                )
        
        else:
            st.markdown("""
            <div class="info-box">
                <h4>💡 How it works:</h4>
                <p>1. Fill in your startup details</p>
                <p>2. Our AI analyzes multiple factors</p>
                <p>3. Get comprehensive valuation estimates</p>
                <p>4. Download detailed reports</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Sample chart
            sample_data = {'low': 500000, 'medium': 2000000, 'high': 5000000}
            fig = create_valuation_chart(sample_data)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # History section
    if st.session_state.valuation_history:
        st.markdown("---")
        st.markdown("### 📊 Valuation History")
        
        for i, entry in enumerate(reversed(st.session_state.valuation_history[-5:])):
            with st.expander(f"🏢 {entry['company']} - {entry['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(entry['valuation'])

# Main application logic
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
