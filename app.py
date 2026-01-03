import streamlit as st
import pandas as pd
import altair as alt
import json
import os
import streamlit.components.v1 as components
from datetime import datetime

# --- APP VERSION ---
APP_VERSION = "v1.0.0"
APP_DATE = "January 2026"

# --- 1. PERSISTENCE ENGINE ---
SAVE_FILE = "retirement_history.json"

def load_all_data():
    """Load all saved year data from JSON file"""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return {}
    return {}

def save_year_data(year, data):
    """Save data for a specific year"""
    all_data = load_all_data()
    all_data[str(year)] = data
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(all_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def delete_year_data(year):
    """Delete data for a specific year"""
    all_data = load_all_data()
    if str(year) in all_data:
        del all_data[str(year)]
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(all_data, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error deleting data: {e}")
            return False
    return False

# --- 2. TAX CALCULATION ENGINE ---
TAX_BRACKETS = [
    {"name": "Floor 1", "low": 0, "high": 53891, "rate": 0.2005},
    {"name": "Floor 2", "low": 53891, "high": 58523, "rate": 0.2415},
    {"name": "Floor 3", "low": 58523, "high": 94907, "rate": 0.2965},
    {"name": "Floor 4", "low": 94907, "high": 117045, "rate": 0.3148},
    {"name": "Floor 5", "low": 117045, "high": 181440, "rate": 0.3389},
    {"name": "Penthouse", "low": 181440, "high": float('inf'), "rate": 0.4797}
]

def calculate_tax_on_income(income):
    """Calculate total tax owed on given income using marginal brackets"""
    if income <= 0:
        return 0
    
    total_tax = 0
    for bracket in TAX_BRACKETS:
        if income > bracket['low']:
            taxable_in_bracket = min(income, bracket['high']) - bracket['low']
            total_tax += taxable_in_bracket * bracket['rate']
    
    return total_tax

def calculate_tax_refund(gross_income, rrsp_contributions):
    """Calculate tax refund from RRSP contributions"""
    if gross_income <= 0:
        return 0
    
    tax_without_rrsp = calculate_tax_on_income(gross_income)
    tax_with_rrsp = calculate_tax_on_income(gross_income - rrsp_contributions)
    refund = tax_without_rrsp - tax_with_rrsp
    
    return max(0, refund)

def get_marginal_rate(income):
    """Get the marginal tax rate for a given income level"""
    if income <= 0:
        return 0
    
    for bracket in TAX_BRACKETS:
        if bracket['low'] <= income < bracket['high']:
            return bracket['rate']
    
    return TAX_BRACKETS[-1]['rate']

def calculate_annual_rrsp(data):
    """
    Calculate total annual RRSP contributions including employer match.
    Employer matches 100% of employee contribution up to the employer_match cap.
    """
    base_salary = data.get('base_salary', 0)
    biweekly_pct = data.get('biweekly_pct', 0)
    employer_match_cap = data.get('employer_match', 0)  # This is the cap %
    
    # Employee contribution
    employee_contrib = base_salary * (biweekly_pct / 100)
    
    # Employer matches up to the cap
    employer_contrib = base_salary * (min(biweekly_pct, employer_match_cap) / 100)
    
    # Periodic contributions (from paychecks)
    periodic_rrsp = employee_contrib + employer_contrib
    
    # Add lump sum contributions
    lump_sum = data.get('rrsp_lump_sum_optimization', 0) + \
                data.get('rrsp_lump_sum_additional', 0) + \
                data.get('rrsp_lump_sum', 0)  # Legacy support
    
    return periodic_rrsp + lump_sum

def is_year_optimized(year_data):
    """Check if a year is optimized (minimizing penthouse exposure)"""
    if not year_data:
        return False
    
    # Calculate values
    t4_gross = year_data.get('t4_gross_income', 0)
    other_inc = year_data.get('other_income', 0)
    total_gross = t4_gross + other_inc
    
    # Use helper function for RRSP calculation
    total_rrsp = calculate_annual_rrsp(year_data)
    taxable_income = max(0, total_gross - total_rrsp)
    
    # Optimized if no penthouse exposure (taxable income under $181,440)
    penthouse_threshold = 181440
    return taxable_income < penthouse_threshold

# --- 3. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="TAX Optimization and TFSA Utilization",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Fintech Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
    }
    
    .premium-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    
    .desc-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(102, 126, 234, 0.4);
    }
    
    .desc-box h4 {
        margin-top: 0;
        color: white;
        font-weight: 600;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 4px solid #3b82f6;
    }
    
    .year-tile {
        background: white;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
        border: 2px solid transparent;
    }
    
    .year-tile:hover {
        box-shadow: 0 8px 16px rgba(0,0,0,0.12);
        transform: translateY(-2px);
        border-color: #3b82f6;
    }
    
    .year-tile-saved {
        border-left: 4px solid #10b981;
    }
    
    .year-tile-empty {
        border-left: 4px solid #94a3b8;
    }
    
    .year-tile-progress {
        border-left: 4px solid #f97316;
    }
    
    .status-saved {
        color: #10b981;
        font-weight: 600;
        margin-top: 8px;
        display: block;
        animation: fadeIn 0.5s;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .priority-high {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
    }
    
    .priority-medium {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left: 4px solid #3b82f6;
    }
    
    h1, h2, h3 {
        font-weight: 600;
        color: #1e293b;
    }
    
    @media print {
        div[data-testid="stSidebar"], 
        .stButton, 
        button:not(.print-button), 
        header, 
        footer, 
        [data-testid="stToolbar"] {
            display: none !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

def description_box(title, content):
    """Render a premium description box"""
    st.markdown(f'''
        <div class="desc-box">
            <h4>{title}</h4>
            <div style="line-height:1.7; font-weight: 300;">{content}</div>
        </div>
    ''', unsafe_allow_html=True)

# --- 4. SESSION STATE INITIALIZATION ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "selected_year" not in st.session_state:
    st.session_state.selected_year = 2025
if "saved_flag" not in st.session_state:
    st.session_state.saved_flag = False
if "refund_to_tfsa" not in st.session_state:
    st.session_state.refund_to_tfsa = 0

# Load all historical data
all_history = load_all_data()

# --- 5. PAGE: HOME ---
if st.session_state.current_page == "Home":
    st.title("🏦 TAX Optimization and TFSA Utilization")
    
    description_box(
        "Strategic Financial Command Center",
        "Welcome to your comprehensive multi-year tax optimization platform. This suite helps you minimize taxes, "
        "maximize RRSP/TFSA contributions, and track portfolio growth across time. "
        "**How to use this dashboard:** (1) Review your global wealth summary to see current portfolio value, "
        "(2) Check the portfolio growth chart to visualize your trajectory, "
        "(3) Select a planning year below to optimize that specific tax year, "
        "(4) Return here to see how your multi-year strategy is performing. "
        "**Green years = optimized, Orange = needs work, Gray = not started.**"
    )
    
    # Global Net Worth Summary
    if all_history:
        st.markdown("### 💎 Global Wealth Summary")
        
        description_box(
            "Portfolio Overview",
            "Your complete financial snapshot showing current balances, lifetime contributions, and tax efficiency gains across all tracked years. "
            "These values represent your projected end-of-year portfolio positions based on your target CAGR."
        )
        
        total_rrsp_all = 0
        total_tfsa_all = 0
        total_tax_shield = 0
        total_contributions = 0
        total_investment_growth = 0
        
        # Get the latest year's ending balance
        latest_year = max(all_history.keys(), key=lambda x: int(x))
        latest_data = all_history[latest_year]
        
        for yr, data in all_history.items():
            t4_gross = data.get('t4_gross_income', 0)
            other_inc = data.get('other_income', 0)
            total_gross = t4_gross + other_inc
            
            # Use helper function for RRSP calculation
            annual_rrsp = calculate_annual_rrsp(data)
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            total_rrsp_all += annual_rrsp
            total_tfsa_all += tfsa_contrib
            total_contributions += annual_rrsp + tfsa_contrib
            
            # Calculate tax shield value
            refund = calculate_tax_refund(total_gross, annual_rrsp)
            total_tax_shield += refund
        
        # Get projected balances from latest year
        if latest_data:
            target_cagr = latest_data.get("target_cagr", 7.0) / 100
            rrsp_start = latest_data.get("rrsp_balance_start", 0)
            tfsa_start = latest_data.get("tfsa_balance_start", 0)
            
            # Use helper function for RRSP calculation
            annual_rrsp = calculate_annual_rrsp(latest_data)
            tfsa_contrib = latest_data.get('tfsa_lump_sum', 0)
            
            # Calculate end of year balances (growth + new contributions)
            rrsp_growth = rrsp_start * target_cagr + annual_rrsp * (target_cagr / 2)
            tfsa_growth = tfsa_start * target_cagr + tfsa_contrib * (target_cagr / 2)
            
            latest_rrsp_balance = rrsp_start + rrsp_growth + annual_rrsp
            latest_tfsa_balance = tfsa_start + tfsa_growth + tfsa_contrib
            
            total_portfolio_value = latest_rrsp_balance + latest_tfsa_balance
            total_investment_growth = total_portfolio_value - total_contributions
        else:
            latest_rrsp_balance = 0
            latest_tfsa_balance = 0
            total_portfolio_value = 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Current RRSP Balance",
                f"${latest_rrsp_balance:,.0f}",
                delta=f"${total_rrsp_all:,.0f} contributed",
                help=f"Projected RRSP value at end of {latest_year}, including all growth and contributions"
            )
        
        with col2:
            st.metric(
                "Current TFSA Balance",
                f"${latest_tfsa_balance:,.0f}",
                delta=f"${total_tfsa_all:,.0f} contributed",
                help=f"Projected TFSA value at end of {latest_year}, including all growth and contributions"
            )
        
        with col3:
            st.metric(
                "Total Tax Shield Value",
                f"${total_tax_shield:,.0f}",
                help="Cumulative tax refunds generated from all RRSP contributions across tracked years"
            )
        
        with col4:
            growth_rate_pct = (total_investment_growth / max(1, total_contributions)) * 100 if total_contributions > 0 else 0
            st.metric(
                "Total Portfolio Value",
                f"${total_portfolio_value:,.0f}",
                delta=f"+${total_investment_growth:,.0f} growth ({growth_rate_pct:.1f}%)",
                help=f"Combined RRSP + TFSA value. Growth represents investment returns above your ${total_contributions:,.0f} total contributions"
            )
        
        # Detailed explanation for Global Wealth Summary
        st.markdown("---")
        st.markdown("#### 📖 Understanding Your Global Wealth Summary")
        st.markdown(f"""
        This dashboard shows your complete retirement portfolio snapshot as of **December {latest_year}** (end of the most recent year you've planned):
        
        **⏰ Important Note About Tax Year Optimization:**
        When optimizing for a specific tax year (e.g., 2025), remember that **RRSP contributions can be claimed until the CRA deadline** - typically the end of February or early March of the following year. This means:
        - **Tax Year 2025** includes all RRSP contributions made from January 1, 2025 through approximately **March 1, 2026**
        - You have the first ~60 days of the new year to finalize your RRSP strategy for the previous tax year
        - Tax optimization typically happens before the end of February, giving you extra time to maximize deductions
        
        ---
        
        **💰 Current RRSP Balance: ${latest_rrsp_balance:,.0f}**
        - This is your projected RRSP account value at the end of {latest_year}
        - Includes all contributions from all years you've tracked: ${total_rrsp_all:,.0f}
        - Includes compound investment growth based on your target CAGR settings
        - This money is tax-deferred (you'll pay tax when you withdraw in retirement)
        
        **🌱 Current TFSA Balance: ${latest_tfsa_balance:,.0f}**
        - This is your projected TFSA account value at the end of {latest_year}
        - Includes all contributions from all years you've tracked: ${total_tfsa_all:,.0f}
        - Includes compound investment growth based on your target CAGR settings
        - This money grows 100% tax-free (no tax when you withdraw, ever!)
        
        **🛡️ Total Tax Shield Value: ${total_tax_shield:,.0f}**
        - This is the total amount of tax refunds you've generated through RRSP contributions
        - Every dollar you contribute to RRSP saves taxes at your marginal rate
        - Example: If you're in the 33.89% bracket, a $10,000 RRSP contribution saves $3,389 in taxes
        - This is "free money" from the government that you can reinvest (ideally into TFSA)
        
        **💎 Total Portfolio Value: ${total_portfolio_value:,.0f}**
        - This is your combined RRSP + TFSA wealth: ${latest_rrsp_balance:,.0f} + ${latest_tfsa_balance:,.0f}
        - You've contributed a total of ${total_contributions:,.0f} across all years
        - Your investments have grown by ${total_investment_growth:,.0f} ({growth_rate_pct:.1f}% return on your contributions)
        - This growth comes from compound investment returns over time
        - **Bottom line**: You put in ${total_contributions:,.0f}, and it's now worth ${total_portfolio_value:,.0f}!
        """)
        
        st.divider()
        
        # Multi-Year Portfolio Growth Chart
        st.markdown("### 📈 Portfolio Growth Over Time")
        
        description_box(
            "Wealth Trajectory Visualization",
            "Track your portfolio's evolution across time. Each year shows two data points: January (start) and December (end). "
            "The stacked areas show how your RRSP (blue) and TFSA (green) accounts grow through contributions and investment returns."
        )
        
        portfolio_history = []
        
        for yr in sorted(all_history.keys(), key=lambda x: int(x)):
            data = all_history[yr]
            
            target_cagr = data.get("target_cagr", 7.0) / 100
            rrsp_start = data.get("rrsp_balance_start", 0)
            tfsa_start = data.get("tfsa_balance_start", 0)
            
            # Use helper function for RRSP calculation
            annual_rrsp = calculate_annual_rrsp(data)
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            # Start of year
            portfolio_history.append({
                "Year": f"{yr} (Jan)",
                "RRSP Balance": rrsp_start,
                "TFSA Balance": tfsa_start,
                "Total": rrsp_start + tfsa_start
            })
            
            # End of year (with growth and contributions)
            rrsp_growth = rrsp_start * target_cagr + annual_rrsp * (target_cagr / 2)
            tfsa_growth = tfsa_start * target_cagr + tfsa_contrib * (target_cagr / 2)
            
            rrsp_end = rrsp_start + rrsp_growth + annual_rrsp
            tfsa_end = tfsa_start + tfsa_growth + tfsa_contrib
            
            portfolio_history.append({
                "Year": f"{yr} (Dec)",
                "RRSP Balance": rrsp_end,
                "TFSA Balance": tfsa_end,
                "Total": rrsp_end + tfsa_end
            })
        
        if portfolio_history:
            df_portfolio = pd.DataFrame(portfolio_history)
            
            # Stacked area chart for portfolio composition
            portfolio_melted = df_portfolio[['Year', 'RRSP Balance', 'TFSA Balance']].melt(
                'Year',
                var_name='Account',
                value_name='Balance'
            )
            
            portfolio_chart = alt.Chart(portfolio_melted).mark_area(
                opacity=0.8,
                line=True
            ).encode(
                x=alt.X('Year:N', title='Timeline', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Balance:Q', title='Portfolio Value ($)', stack='zero'),
                color=alt.Color('Account:N',
                    scale=alt.Scale(
                        domain=['RRSP Balance', 'TFSA Balance'],
                        range=['#3b82f6', '#10b981']
                    ),
                    legend=alt.Legend(title="Account Type")
                ),
                tooltip=[
                    alt.Tooltip('Year:N', title='Period'),
                    alt.Tooltip('Account:N', title='Account'),
                    alt.Tooltip('Balance:Q', title='Balance', format='$,.0f')
                ]
            ).properties(height=400)
            
            st.altair_chart(portfolio_chart, use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### 📖 How to Read Your Portfolio Growth Chart")
            st.markdown("""
            This stacked area chart shows how your retirement portfolio has grown over time. Here's what you're seeing:
            
            **📊 The Colored Areas:**
            - **Blue area (bottom)**: Your RRSP account balance over time
            - **Green area (top)**: Your TFSA account balance stacked on top
            - **Total height**: Your complete portfolio value (RRSP + TFSA combined)
            
            **📅 The Timeline (X-Axis):**
            - Each year appears TWICE: once for January (start of year) and once for December (end of year)
            - **January markers**: Show your portfolio value on January 1st, before making any new contributions that year
            - **December markers**: Show your portfolio value on December 31st, after all contributions and investment growth
            
            **📈 What the Growth Represents:**
            - **Vertical jumps from Jan → Dec**: This is your contributions PLUS investment returns for that year
            - **Vertical jumps from Dec → next Jan**: Usually flat (representing year rollover)
            - **Overall upward slope**: Shows your wealth-building momentum over multiple years
            
            **💡 Key Insights to Look For:**
            1. **Steeper slopes** = faster wealth accumulation (higher contributions or better returns)
            2. **Blue getting bigger** = RRSP growing (tax-deferred, good for retirement)
            3. **Green getting bigger** = TFSA growing (tax-free, good for any goal)
            4. **Consistent pattern** = disciplined, systematic saving (the best path to wealth)
            
            **🎯 Example Reading:**
            - If you see a big jump from 2025 Dec to 2026 Dec, that means you made significant contributions in 2026 AND/OR had strong investment returns
            - If the chart is mostly blue, you're focusing on tax-deferred RRSP savings
            - If the chart has more green, you're prioritizing tax-free TFSA growth
            - The ideal strategy typically uses BOTH accounts strategically
            """)
            
            # Summary stats
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            st.markdown("#### 📊 Portfolio Performance Metrics")
            st.markdown("""
                These metrics summarize your portfolio's performance across all tracked years:
                - **Total Growth**: Dollar amount your portfolio has grown beyond contributions
                - **Annualized Return (CAGR)**: Your average annual return rate - compare this to your target CAGR
                - **Years Tracked**: How many years of data you've entered for analysis
            """)
            
            first_total = df_portfolio.iloc[0]['Total']
            last_total = df_portfolio.iloc[-1]['Total']
            total_return = last_total - first_total
            total_return_pct = (total_return / max(1, first_total)) * 100 if first_total > 0 else 0
            
            # Calculate actual time span (from first Jan to last Dec)
            first_year = int(df_portfolio.iloc[0]['Year'].split()[0])
            last_year = int(df_portfolio.iloc[-1]['Year'].split()[0])
            years_span = last_year - first_year + 1  # Include both start and end year
            
            with col_stats1:
                st.metric(
                    "Total Growth",
                    f"${total_return:,.0f}",
                    delta=f"+{total_return_pct:.1f}%",
                    help=f"Portfolio growth from {first_year} to {last_year}"
                )
            
            with col_stats2:
                # CAGR formula: ((Ending Value / Beginning Value)^(1/years)) - 1
                annualized_return = ((last_total / max(1, first_total)) ** (1 / max(1, years_span)) - 1) * 100 if first_total > 0 and years_span > 0 else 0
                st.metric(
                    "Annualized Return (CAGR)",
                    f"{annualized_return:.2f}%",
                    help=f"Compound annual growth rate over {years_span} year{'s' if years_span != 1 else ''}"
                )
            
            with col_stats3:
                st.metric(
                    "Years Tracked",
                    f"{len(all_history)}",
                    help="Number of years with saved data"
                )
        
        st.divider()
    
    # Planning Years Grid
    st.markdown("### 📅 Planning Years")
    
    description_box(
        "Year-by-Year Strategy Navigator",
        "Select any year to view detailed tax optimization strategies. Each tile shows optimization status: "
        "Empty years need data entry, In Progress years need additional RRSP contributions to avoid high tax brackets, "
        "and Optimized years have achieved maximum tax efficiency."
    )
    
    # Status Legend
    st.markdown("""
        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <strong>📊 Year Status Legend:</strong>
            <span style="margin-left: 20px;">⚪ <strong>Empty</strong> - No data saved yet</span>
            <span style="margin-left: 20px;">🟠 <strong>In Progress</strong> - Has data but taxable income ≥ $181,440 (Penthouse exposure)</span>
            <span style="margin-left: 20px;">🟢 <strong>Optimized</strong> - Fully optimized with taxable income < $181,440</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Add/Remove year functionality
    st.markdown("#### ⚙️ Manage Planning Years")
    col_add1, col_add2, col_add3, col_add4 = st.columns([2, 1, 2, 1])
    
    with col_add1:
        new_year_input = st.number_input(
            "Year to Add",
            min_value=2020,
            max_value=2050,
            value=2031,
            step=1,
            key="new_year_input",
            help="Enter a year between 2020-2050 to add to your planning grid"
        )
    
    with col_add2:
        if st.button("➕ Add Year", use_container_width=True, type="primary"):
            if str(new_year_input) not in all_history:
                # Create empty year entry
                save_year_data(new_year_input, {
                    "t4_gross_income": 0,
                    "other_income": 0,
                    "base_salary": 0,
                    "biweekly_pct": 0,
                    "employer_match": 0,
                    "rrsp_lump_sum_optimization": 0,
                    "rrsp_lump_sum_additional": 0,
                    "tfsa_lump_sum": 0,
                    "rrsp_room": 0,
                    "tfsa_room": 0,
                    "rrsp_balance_start": 0,
                    "tfsa_balance_start": 0,
                    "target_cagr": 7.0
                })
                st.success(f"✓ Year {new_year_input} added successfully!")
                st.rerun()
            else:
                st.error(f"✗ Year {new_year_input} already exists!")
    
    with col_add3:
        if len(all_history) > 0:
            years_to_delete = [int(yr) for yr in all_history.keys()]
            delete_year_input = st.selectbox(
                "Year to Remove",
                options=sorted(years_to_delete, reverse=True),
                key="delete_year_input",
                help="Select a saved year to permanently remove from your planning"
            )
        else:
            delete_year_input = None
            st.info("💡 No saved years to remove yet")
    
    with col_add4:
        if delete_year_input and len(all_history) > 0:
            if st.button("🗑️ Remove", use_container_width=True):
                if delete_year_data(delete_year_input):
                    st.success(f"✓ Year {delete_year_input} removed successfully!")
                    st.rerun()
                else:
                    st.error(f"✗ Failed to remove year {delete_year_input}")
    
    st.divider()
    
    # Get all years (saved + default range)
    all_years = set(range(2024, 2031))
    all_years.update([int(yr) for yr in all_history.keys()])
    years_to_show = sorted(list(all_years))
    
    cols_per_row = 4
    
    for row_start in range(0, len(years_to_show), cols_per_row):
        cols = st.columns(cols_per_row)
        for i, yr in enumerate(years_to_show[row_start:row_start + cols_per_row]):
            with cols[i]:
                is_saved = str(yr) in all_history
                is_optimized = is_year_optimized(all_history.get(str(yr), {})) if is_saved else False
                
                # Determine status and styling
                if not is_saved:
                    # Gray/Slate - Empty
                    status_emoji = "⚪"
                    status_text = "Empty"
                    button_label = f"📅 **{yr}**\n{status_emoji} {status_text}"
                    container_style = "background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); border: 2px solid #94a3b8; border-radius: 12px; padding: 4px;"
                elif is_optimized:
                    # Green - Optimized
                    data = all_history[str(yr)]
                    annual_rrsp = calculate_annual_rrsp(data)
                    status_emoji = "🟢"
                    status_text = f"${annual_rrsp:,.0f}"
                    button_label = f"📅 **{yr}**\n{status_text}\n{status_emoji} Optimized"
                    container_style = "background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border: 2px solid #10b981; border-radius: 12px; padding: 4px;"
                else:
                    # Orange - In Progress
                    data = all_history[str(yr)]
                    annual_rrsp = calculate_annual_rrsp(data)
                    status_emoji = "🟠"
                    status_text = f"${annual_rrsp:,.0f}"
                    button_label = f"📅 **{yr}**\n{status_text}\n{status_emoji} In Progress"
                    container_style = "background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%); border: 2px solid #f97316; border-radius: 12px; padding: 4px;"
                
                # Wrap button in styled container
                st.markdown(f'<div style="{container_style}">', unsafe_allow_html=True)
                
                # Create the button
                if st.button(
                    button_label,
                    key=f"home_{yr}",
                    use_container_width=True,
                    type="primary" if is_saved else "secondary"
                ):
                    st.session_state.selected_year = yr
                    st.session_state.current_page = "Year View"
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Multi-Year Analytics
    if all_history and len(all_history) > 1:
        st.divider()
        st.markdown("### 📈 Multi-Year Analytics & Trends")
        
        description_box(
            "Comparative Analysis Dashboard",
            "Analyze patterns and trends across multiple years. The burndown charts show how efficiently you're using available contribution room. "
            "Income charts reveal your tax-shielding effectiveness. Contribution trends help you plan future savings strategies."
        )
        
        # Prepare data for charts
        chart_data = []
        room_data = []
        burndown_data = []
        
        for yr, data in sorted(all_history.items(), key=lambda x: x[0]):
            t4_gross = data.get('t4_gross_income', 0)
            other_inc = data.get('other_income', 0)
            total_gross = t4_gross + other_inc
            
            # Use helper function for RRSP calculation
            annual_rrsp = calculate_annual_rrsp(data)
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            rrsp_room_avail = data.get('rrsp_room', 0)
            tfsa_room_avail = data.get('tfsa_room', 0)
            
            chart_data.append({
                "Year": yr,
                "Gross Income": total_gross,
                "Taxable Income": total_gross - annual_rrsp,
                "Tax Shield": annual_rrsp,
                "RRSP": annual_rrsp,
                "TFSA": tfsa_contrib
            })
            
            room_data.append({
                "Year": yr,
                "Account": "RRSP",
                "Remaining Room": max(0, rrsp_room_avail - annual_rrsp)
            })
            room_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Remaining Room": max(0, tfsa_room_avail - tfsa_contrib)
            })
            
            # Burndown data - showing used vs available
            burndown_data.append({
                "Year": yr,
                "Account": "RRSP",
                "Status": "Used",
                "Amount": annual_rrsp
            })
            burndown_data.append({
                "Year": yr,
                "Account": "RRSP",
                "Status": "Available",
                "Amount": max(0, rrsp_room_avail - annual_rrsp)
            })
            burndown_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Status": "Used",
                "Amount": tfsa_contrib
            })
            burndown_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Status": "Available",
                "Amount": max(0, tfsa_room_avail - tfsa_contrib)
            })
        
        df_chart = pd.DataFrame(chart_data)
        df_room = pd.DataFrame(room_data)
        df_burndown = pd.DataFrame(burndown_data)
        
        # RRSP & TFSA Burndown Charts
        st.markdown("**Contribution Room Burndown Analysis**")
        
        description_box(
            "Room Utilization Efficiency",
            "These stacked bar charts show how much of your available contribution room you're actually using each year. "
            "Green/Blue represents room you've used (good!), gray shows unused room (opportunity cost). "
            "Higher utilization percentages mean you're maximizing your tax-advantaged space."
        )
        
        col_burn1, col_burn2 = st.columns(2)
        
        with col_burn1:
            st.markdown("**RRSP Room Utilization**")
            
            rrsp_burndown = df_burndown[df_burndown['Account'] == 'RRSP']
            
            rrsp_chart = alt.Chart(rrsp_burndown).mark_bar().encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Amount:Q', title='RRSP Room ($)', stack='zero'),
                color=alt.Color('Status:N',
                    scale=alt.Scale(
                        domain=['Used', 'Available'],
                        range=['#10b981', '#e2e8f0']
                    ),
                    legend=alt.Legend(title="Room Status")
                ),
                tooltip=[
                    alt.Tooltip('Year:N', title='Year'),
                    alt.Tooltip('Status:N', title='Status'),
                    alt.Tooltip('Amount:Q', title='Amount', format='$,.0f')
                ]
            ).properties(height=320)
            
            st.altair_chart(rrsp_chart, use_container_width=True)
            
            st.markdown("**📖 Understanding This Chart:**")
            st.markdown("""
                - **Green bars**: RRSP room you've used (contributions made)
                - **Gray bars**: RRSP room left unused (missed opportunity)
                - **Taller green = better**: You're maximizing tax-advantaged space
                - **Goal**: Minimize gray, maximize green for optimal tax efficiency
            """)
            
            # Calculate average utilization
            total_used = rrsp_burndown[rrsp_burndown['Status'] == 'Used']['Amount'].sum()
            total_available = rrsp_burndown['Amount'].sum()
            utilization = (total_used / total_available * 100) if total_available > 0 else 0
            st.metric("Avg RRSP Utilization", f"{utilization:.1f}%")
        
        with col_burn2:
            st.markdown("**TFSA Room Utilization**")
            
            tfsa_burndown = df_burndown[df_burndown['Account'] == 'TFSA']
            
            tfsa_chart = alt.Chart(tfsa_burndown).mark_bar().encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Amount:Q', title='TFSA Room ($)', stack='zero'),
                color=alt.Color('Status:N',
                    scale=alt.Scale(
                        domain=['Used', 'Available'],
                        range=['#3b82f6', '#e2e8f0']
                    ),
                    legend=alt.Legend(title="Room Status")
                ),
                tooltip=[
                    alt.Tooltip('Year:N', title='Year'),
                    alt.Tooltip('Status:N', title='Status'),
                    alt.Tooltip('Amount:Q', title='Amount', format='$,.0f')
                ]
            ).properties(height=320)
            
            st.altair_chart(tfsa_chart, use_container_width=True)
            
            st.markdown("**📖 Understanding This Chart:**")
            st.markdown("""
                - **Blue bars**: TFSA room you've used (contributions made)
                - **Gray bars**: TFSA room left unused (missed opportunity)
                - **Why it matters**: Unused TFSA room accumulates, but you miss years of tax-free growth
                - **Strategy tip**: Deploy your RRSP tax refunds here for compounding tax-free returns
            """)
            
            # Calculate average utilization
            total_used = tfsa_burndown[tfsa_burndown['Status'] == 'Used']['Amount'].sum()
            total_available = tfsa_burndown['Amount'].sum()
            utilization = (total_used / total_available * 100) if total_available > 0 else 0
            st.metric("Avg TFSA Utilization", f"{utilization:.1f}%")
        
        st.divider()
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("**Income vs. Tax-Shielded Income**")
            
            description_box(
                "Tax Efficiency Comparison",
                "This side-by-side bar chart compares your gross income (what you earned) against your taxable income (what you pay tax on). "
                "The difference represents income you've successfully shielded from taxes using RRSP contributions. "
                "Bigger gaps mean more tax savings!"
            )
            
            income_df = df_chart[['Year', 'Gross Income', 'Taxable Income']].melt(
                'Year',
                var_name='Category',
                value_name='Amount'
            )
            
            income_chart = alt.Chart(income_df).mark_bar(opacity=0.85).encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Amount:Q', title='Income ($)'),
                color=alt.Color('Category:N',
                    scale=alt.Scale(
                        domain=['Gross Income', 'Taxable Income'],
                        range=['#94a3b8', '#3b82f6']
                    ),
                    legend=alt.Legend(title="Income Type")
                ),
                xOffset='Category:N'
            ).properties(height=320)
            
            st.altair_chart(income_chart, use_container_width=True)
            
            st.markdown("**📖 Understanding This Chart:**")
            st.markdown("""
                - **Gray bars**: Your total gross income (before RRSP deductions)
                - **Blue bars**: Your taxable income (after RRSP deductions)
                - **The gap between bars**: Amount you've shielded from taxes
                - **Bigger gap = bigger tax savings**: More income protected at your marginal rate
                - **Goal**: Keep blue bars below $181,440 to avoid 47.97% Penthouse bracket
            """)
        
        with col_right:
            st.markdown("**Remaining Room Trajectory**")
            
            description_box(
                "Year-End Room Availability",
                "This chart shows how much contribution room you have left at the END of each year, after all contributions. "
                "Room doesn't disappear - it carries forward! But leaving room unused means missing years of tax-advantaged growth. "
                "Downward trends are normal as you consume room, but CRA adds new room each year."
            )
            
            room_chart = alt.Chart(df_room).mark_area(
                opacity=0.7,
                line=True
            ).encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Remaining Room:Q', title='Remaining Room ($)'),
                color=alt.Color('Account:N',
                    scale=alt.Scale(
                        domain=['RRSP', 'TFSA'],
                        range=['#3b82f6', '#10b981']
                    ),
                    legend=alt.Legend(title="Account")
                )
            ).properties(height=320)
            
            st.altair_chart(room_chart, use_container_width=True)
        
        # Contribution trends
        st.markdown("**Annual Contribution Trends**")
        
        description_box(
            "Contribution Consistency Analysis",
            "This line chart tracks your yearly contribution amounts for both RRSP and TFSA. "
            "**Look for**: (1) Upward trends as income grows, (2) Consistent patterns showing disciplined saving, "
            "(3) Gaps where you might have missed opportunities. "
            "Steady or increasing contributions build long-term wealth through compound growth."
        )
        
        contrib_df = df_chart[['Year', 'RRSP', 'TFSA']].melt(
            'Year',
            var_name='Account',
            value_name='Contribution'
        )
        
        contrib_chart = alt.Chart(contrib_df).mark_line(
            point=alt.OverlayMarkDef(filled=False, fill="white", size=80)
        ).encode(
            x=alt.X('Year:N', title='Year'),
            y=alt.Y('Contribution:Q', title='Annual Contribution ($)'),
            color=alt.Color('Account:N',
                scale=alt.Scale(
                    domain=['RRSP', 'TFSA'],
                    range=['#3b82f6', '#10b981']
                )
            ),
            strokeWidth=alt.value(3)
        ).properties(height=300)
        
        st.altair_chart(contrib_chart, use_container_width=True)

# --- 6. PAGE: YEAR VIEW ---
else:
    selected_year = st.session_state.selected_year
    year_data = all_history.get(str(selected_year), {})

    with st.sidebar:
        if st.button("⬅️ Back to Home", use_container_width=True):
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.header(f"⚙️ {selected_year} Parameters")
        
        with st.form(key="input_form"):
            st.markdown("### 💵 Income Parameters")
            
            t4_gross_income = st.number_input(
                "Annual T4 Gross Income",
                value=float(year_data.get("t4_gross_income", 0)),
                step=5000.0,
                min_value=0.0,
                help="Total employment income from Box 14 of your T4"
            )
            
            other_income = st.number_input(
                "Other Income",
                value=float(year_data.get("other_income", 0)),
                step=1000.0,
                min_value=0.0,
                help="Additional taxable income (e.g., rental property net income after expenses)"
            )
            
            base_salary = st.number_input(
                "Annual Base Salary",
                value=float(year_data.get("base_salary", 0)),
                step=5000.0,
                min_value=0.0,
                help="Core salary used for percentage-based contributions"
            )
            
            st.caption(f"💰 Total Gross Income: ${t4_gross_income + other_income:,.0f}")
            
            st.markdown("### 🎯 RRSP Strategy")
            
            biweekly_pct = st.slider(
                "Biweekly RRSP Contribution (%)",
                0.0, 18.0,
                value=float(year_data.get("biweekly_pct", 0.0)),
                step=0.5,
                help="Percentage of base salary you contribute from each paycheck"
            )
            
            employer_match_cap = st.slider(
                "Employer Match Cap (% of Base Salary)",
                0.0, 10.0,
                value=float(year_data.get("employer_match", 4.0)),
                step=0.5,
                help="Employer matches 100% of YOUR contribution up to this % of base salary. Example: 4% cap means if you contribute 6%, employer only matches up to 4%"
            )
            
            # Calculate actual employer contribution
            employee_contribution_pct = biweekly_pct
            employer_contribution_pct = min(employee_contribution_pct, employer_match_cap)
            
            st.caption(f"💡 Your contribution: {employee_contribution_pct:.1f}% (${base_salary * employee_contribution_pct / 100:,.0f}) | "
                      f"Employer matches: {employer_contribution_pct:.1f}% (${base_salary * employer_contribution_pct / 100:,.0f})")
            
            if employee_contribution_pct > employer_match_cap:
                st.warning(f"⚠️ You're contributing {employee_contribution_pct:.1f}% but employer only matches up to {employer_match_cap:.1f}%. "
                          f"You're contributing ${base_salary * (employee_contribution_pct - employer_match_cap) / 100:,.0f} beyond the match.")
            elif employee_contribution_pct < employer_match_cap:
                missed_match = base_salary * (employer_match_cap - employee_contribution_pct) / 100
                st.info(f"💰 Opportunity: Increase contribution to {employer_match_cap:.1f}% to get ${missed_match:,.0f} more in free employer money!")
            
            rrsp_lump_sum_optimization = st.number_input(
                "RRSP Lump Sum (Tax Optimization)",
                value=float(year_data.get("rrsp_lump_sum_optimization", 0)),
                step=1000.0,
                min_value=0.0,
                help="Strategic deposit to optimize tax bracket positioning"
            )
            
            rrsp_lump_sum_additional = st.number_input(
                "RRSP Lump Sum (Additional Refund)",
                value=float(year_data.get("rrsp_lump_sum_additional", 0)),
                step=1000.0,
                min_value=0.0,
                help="Extra contributions to maximize tax refund beyond optimization"
            )
            
            st.caption(f"💰 Total RRSP Lump Sum: ${rrsp_lump_sum_optimization + rrsp_lump_sum_additional:,.0f}")
            
            st.markdown("### 🌱 TFSA Strategy")
            
            tfsa_lump_sum = st.number_input(
                "TFSA Lump Sum Deposit",
                value=float(year_data.get("tfsa_lump_sum", 0)),
                step=1000.0,
                min_value=0.0,
                help="Tax-free savings account contribution"
            )
            
            st.markdown("### 📋 CRA Contribution Limits")
            
            # Get default values from previous year if available
            prev_year = str(selected_year - 1)
            default_rrsp_room = 0.0
            default_tfsa_room = 0.0
            
            if prev_year in all_history:
                prev_data = all_history[prev_year]
                
                # Calculate remaining room from previous year using helper function
                prev_annual_rrsp = calculate_annual_rrsp(prev_data)
                prev_tfsa_contrib = prev_data.get('tfsa_lump_sum', 0)
                
                prev_rrsp_room_remaining = max(0, prev_data.get('rrsp_room', 0) - prev_annual_rrsp)
                prev_tfsa_room_remaining = max(0, prev_data.get('tfsa_room', 0) - prev_tfsa_contrib)
                
                # Add new room for current year (based on previous year's total gross income)
                prev_t4_gross = prev_data.get('t4_gross_income', 0)
                prev_other_income = prev_data.get('other_income', 0)
                prev_total_gross = prev_t4_gross + prev_other_income
                
                new_rrsp_room = min(31560, prev_total_gross * 0.18)
                new_tfsa_room = 7000
                
                default_rrsp_room = prev_rrsp_room_remaining + new_rrsp_room
                default_tfsa_room = prev_tfsa_room_remaining + new_tfsa_room
            
            rrsp_room = st.number_input(
                "Available RRSP Room",
                value=float(year_data.get("rrsp_room", default_rrsp_room)),
                step=1000.0,
                min_value=0.0,
                help="From your latest Notice of Assessment (auto-filled from previous year if available)"
            )
            
            tfsa_room = st.number_input(
                "Available TFSA Room",
                value=float(year_data.get("tfsa_room", default_tfsa_room)),
                step=1000.0,
                min_value=0.0,
                help="From CRA MyAccount (auto-filled from previous year if available)"
            )
            
            if prev_year in all_history and default_rrsp_room > 0:
                st.caption(f"ℹ️ Auto-calculated from {prev_year} carryover + new room")
            
            st.markdown("### 📈 Portfolio Tracking")
            
            # Calculate default values from previous year's end balances
            prev_year = str(selected_year - 1)
            default_rrsp_balance = 0.0
            default_tfsa_balance = 0.0
            
            if prev_year in all_history:
                prev_data = all_history[prev_year]
                
                # Get previous year's values
                prev_target_cagr = prev_data.get("target_cagr", 7.0) / 100
                prev_rrsp_start = prev_data.get("rrsp_balance_start", 0)
                prev_tfsa_start = prev_data.get("tfsa_balance_start", 0)
                
                # Calculate previous year's contributions using helper function
                prev_annual_rrsp = calculate_annual_rrsp(prev_data)
                prev_tfsa_contrib = prev_data.get('tfsa_lump_sum', 0)
                
                # Calculate previous year's growth
                prev_rrsp_growth = prev_rrsp_start * prev_target_cagr + prev_annual_rrsp * (prev_target_cagr / 2)
                prev_tfsa_growth = prev_tfsa_start * prev_target_cagr + prev_tfsa_contrib * (prev_target_cagr / 2)
                
                # End balances become start balances for current year
                default_rrsp_balance = prev_rrsp_start + prev_rrsp_growth + prev_annual_rrsp
                default_tfsa_balance = prev_tfsa_start + prev_tfsa_growth + prev_tfsa_contrib
            
            rrsp_balance_start = st.number_input(
                "RRSP Balance (Start of Year)",
                value=float(year_data.get("rrsp_balance_start", default_rrsp_balance)),
                step=1000.0,
                min_value=0.0,
                help="Total RRSP portfolio value on January 1st (auto-calculated from previous year if available)"
            )
            
            tfsa_balance_start = st.number_input(
                "TFSA Balance (Start of Year)",
                value=float(year_data.get("tfsa_balance_start", default_tfsa_balance)),
                step=1000.0,
                min_value=0.0,
                help="Total TFSA portfolio value on January 1st (auto-calculated from previous year if available)"
            )
            
            if prev_year in all_history and default_rrsp_balance > 0:
                st.caption(f"ℹ️ Auto-calculated from {prev_year} end-of-year projected balances")
            
            target_cagr = st.slider(
                "Target Annual Return (CAGR %)",
                0.0, 50.0,
                value=float(year_data.get("target_cagr", 7.0)),
                step=0.5,
                help="Expected compound annual growth rate for investments (0-50%)"
            )
            
            st.caption(f"📊 Using {target_cagr}% CAGR for growth projections")
            
            st.divider()
            
            # Form submit buttons
            col_save, col_reset = st.columns(2)
            
            with col_save:
                submitted = st.form_submit_button(
                    "💾 Save",
                    use_container_width=True,
                    type="primary"
                )
            
            with col_reset:
                reset = st.form_submit_button(
                    "🔄 Reset",
                    use_container_width=True
                )
            
            if submitted:
                success = save_year_data(selected_year, {
                    "t4_gross_income": t4_gross_income,
                    "other_income": other_income,
                    "base_salary": base_salary,
                    "biweekly_pct": biweekly_pct,
                    "employer_match": employer_match_cap,
                    "rrsp_lump_sum_optimization": rrsp_lump_sum_optimization,
                    "rrsp_lump_sum_additional": rrsp_lump_sum_additional,
                    "tfsa_lump_sum": tfsa_lump_sum,
                    "rrsp_room": rrsp_room,
                    "tfsa_room": tfsa_room,
                    "rrsp_balance_start": rrsp_balance_start,
                    "tfsa_balance_start": tfsa_balance_start,
                    "target_cagr": target_cagr
                })
                
                if success:
                    st.session_state.saved_flag = True
                    st.rerun()
            
            if reset:
                delete_year_data(selected_year)
                st.rerun()
        
        if st.session_state.get("saved_flag"):
            st.success("✓ Strategy saved successfully!")
            st.session_state.saved_flag = False
    
    # Main content area - Calculations
    other_income = year_data.get("other_income", 0)
    total_gross_income = t4_gross_income + other_income
    
    # Calculate RRSP contributions with correct employer matching logic
    employee_rrsp_contribution = base_salary * (biweekly_pct / 100)
    employer_rrsp_contribution = base_salary * (min(biweekly_pct, employer_match_cap) / 100)
    annual_rrsp_periodic = employee_rrsp_contribution + employer_rrsp_contribution
    
    rrsp_lump_sum = rrsp_lump_sum_optimization + rrsp_lump_sum_additional
    total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
    taxable_income = max(0, total_gross_income - total_rrsp_contributions)
    
    # Portfolio calculations
    rrsp_balance_start = year_data.get("rrsp_balance_start", 0)
    tfsa_balance_start = year_data.get("tfsa_balance_start", 0)
    target_cagr = year_data.get("target_cagr", 7.0) / 100  # Convert to decimal
    
    # Calculate end of year balances (growth + new contributions)
    # Assuming contributions happen throughout the year, use half-year growth on new money
    rrsp_growth_existing = rrsp_balance_start * target_cagr
    rrsp_growth_new_contrib = total_rrsp_contributions * (target_cagr / 2)  # Half year average
    rrsp_balance_end = rrsp_balance_start + rrsp_growth_existing + total_rrsp_contributions + rrsp_growth_new_contrib
    
    tfsa_growth_existing = tfsa_balance_start * target_cagr
    tfsa_growth_new_contrib = tfsa_lump_sum * (target_cagr / 2)
    tfsa_balance_end = tfsa_balance_start + tfsa_growth_existing + tfsa_lump_sum + tfsa_growth_new_contrib
    
    total_portfolio_value = rrsp_balance_end + tfsa_balance_end
    
    # Calculate tax refund
    estimated_refund = calculate_tax_refund(total_gross_income, total_rrsp_contributions)
    marginal_rate = get_marginal_rate(total_gross_income)
    
    # Optimization status
    penthouse_threshold = 181440
    is_optimized = taxable_income < penthouse_threshold
    
    # Remaining room calculations
    remaining_rrsp_room = max(0, rrsp_room - total_rrsp_contributions)
    remaining_tfsa_room = max(0, tfsa_room - tfsa_lump_sum)
    
    # Header
    st.title(f"🏛️ Tax Optimization Strategy: {selected_year}")
    
    # Status Card
    col_status1, col_status2 = st.columns([3, 1])
    
    with col_status1:
        description_box(
            "Strategic Execution Framework",
            f"Follow this comprehensive plan to maximize your tax efficiency and wealth velocity for {selected_year}. "
            "Each section provides actionable insights to optimize your contribution strategy."
        )
    
    with col_status2:
        if is_optimized:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                     padding: 20px; border-radius: 12px; border: 2px solid #10b981; text-align: center;">
                    <div style="font-size: 3em;">🟢</div>
                    <div style="font-size: 1.2em; font-weight: 600; color: #065f46; margin-top: 10px;">
                        OPTIMIZED
                    </div>
                    <div style="font-size: 0.9em; color: #047857; margin-top: 5px;">
                        This year will show GREEN
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%); 
                     padding: 20px; border-radius: 12px; border: 2px solid #f97316; text-align: center;">
                    <div style="font-size: 3em;">🟠</div>
                    <div style="font-size: 1.2em; font-weight: 600; color: #7c2d12; margin-top: 10px;">
                        IN PROGRESS
                    </div>
                    <div style="font-size: 0.9em; color: #9a3412; margin-top: 5px;">
                        More RRSP needed
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    # Key Metrics Dashboard
    st.markdown("### 📊 Strategic Overview")
    
    if other_income > 0:
        st.info(f"💼 Income Breakdown: T4 ${t4_gross_income:,.0f} + Other ${other_income:,.0f} = Total ${total_gross_income:,.0f}")
    
    # Optimization Status Banner
    if is_optimized:
        st.success(f"🟢 **OPTIMIZED** - Your taxable income (${taxable_income:,.0f}) is below the Penthouse threshold (${penthouse_threshold:,.0f}). This year will show GREEN on the home page.")
    else:
        deficit = taxable_income - penthouse_threshold
        additional_rrsp_needed = deficit
        st.warning(f"🟠 **IN PROGRESS** - Your taxable income (${taxable_income:,.0f}) exceeds the Penthouse threshold by ${deficit:,.0f}. "
                  f"Add ${additional_rrsp_needed:,.0f} more to RRSP contributions to achieve GREEN optimization status and save ${deficit * 0.4797:,.0f} in taxes.")
        
        # Pending Items Checklist
        st.markdown("### ✅ Pending Items to Reach Optimization")
        
        pending_items = []
        
        # Item 1: RRSP contribution needed
        if deficit > 0:
            pending_items.append({
                "item": "Increase RRSP Contributions",
                "current": f"${total_rrsp_contributions:,.0f}",
                "target": f"${total_rrsp_contributions + deficit:,.0f}",
                "action": f"Add ${deficit:,.0f} to either 'RRSP Lump Sum (Tax Optimization)' or 'RRSP Lump Sum (Additional Refund)' in the sidebar",
                "impact": f"Saves ${deficit * 0.4797:,.0f} in taxes at 47.97% Penthouse rate"
            })
        
        # Item 2: Room availability check
        if deficit > remaining_rrsp_room:
            pending_items.append({
                "item": "⚠️ Insufficient RRSP Room",
                "current": f"${remaining_rrsp_room:,.0f} available",
                "target": f"${deficit:,.0f} needed",
                "action": f"You need ${deficit - remaining_rrsp_room:,.0f} more RRSP room than available. Consider: (1) Verify your NOA room is correct, (2) Use spousal RRSP if married, (3) Accept partial optimization this year",
                "impact": "May not achieve full green status this year"
            })
        
        if pending_items:
            for idx, item in enumerate(pending_items, 1):
                st.markdown(f"""
                    <div class="premium-card" style="border-left: 4px solid #f59e0b;">
                        <h4>Item {idx}: {item['item']}</h4>
                        <p><strong>Current:</strong> {item['current']} | <strong>Target:</strong> {item['target']}</p>
                        <p><strong>Action Required:</strong> {item['action']}</p>
                        <p style="color: #059669;"><strong>Impact:</strong> {item['impact']}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No pending items - year is optimized!")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Gross Income",
            f"${total_gross_income:,.0f}",
            delta=f"+${other_income:,.0f} other" if other_income > 0 else None,
            help="T4 employment income plus other taxable income"
        )
    
    with col2:
        st.metric(
            "Taxable Income",
            f"${taxable_income:,.0f}",
            delta=f"-${total_rrsp_contributions:,.0f}",
            delta_color="inverse",
            help="Income after RRSP deductions"
        )
    
    with col3:
        st.metric(
            "Marginal Tax Rate",
            f"{marginal_rate*100:.2f}%",
            help="Your current tax bracket rate"
        )
    
    with col4:
        st.metric(
            "Estimated Tax Refund",
            f"${estimated_refund:,.0f}",
            delta=f"+{(estimated_refund/max(1,total_rrsp_contributions))*100:.1f}% ROI",
            help="Tax refund from RRSP contributions"
        )
    
    with col5:
        st.metric(
            "Total Portfolio Value",
            f"${total_portfolio_value:,.0f}",
            delta=f"+{target_cagr*100:.1f}% target",
            help="Combined RRSP + TFSA projected end-of-year value"
        )
    
    st.info("ℹ️ For full year view details, charts, and insights, please return to the Home page.")

# Footer
st.divider()
current_date = datetime.now().strftime("%B %d, %Y")
st.markdown(f"""
    <div style="text-align: center; color: #64748b; padding: 20px;">
        <p><strong>TAX Optimization and TFSA Utilization</strong></p>
        <p style="font-size: 0.9em;">
            Tax rates are based on 2025/2026 Ontario combined federal + provincial brackets. 
            Always consult with a qualified tax professional for personalized advice.
        </p>
        <p style="font-size: 0.85em; margin-top: 10px;">
            RRSP contribution limit: 18% of previous year's income (max $31,560) | 
            TFSA annual limit: $7,000
        </p>
        <p style="font-size: 0.75em; margin-top: 15px; color: #94a3b8;">
            Version {APP_VERSION} • {APP_DATE} • Generated on {current_date}
        </p>
    </div>
""", unsafe_allow_html=True)
