import streamlit as st
import math

st.title("熱敏電阻過熱保護計算器")

# 熱敏電阻類型
therm_type = st.radio("熱敏電阻類型", ["NTC", "PTC"])

# 觸發倍率，可修改
col1, col2 = st.columns(2)
with col1:
    X = st.text_input("NTC 觸發倍率 X", value="0.45")
with col2:
    Y = st.text_input("PTC 觸發倍率 Y", value="0.8")

# 其他參數
R25_val = st.text_input("R25 (Ω)", value="")  # 可留空
B_val = st.text_input("B 值", value="3950")
Vcc_val = st.text_input("VCC (V)", value="5")
R1_val = st.text_input("R1 (Ω)", value="")  # 可留空
Tt_val = st.text_input("目標溫度 (°C)", value="")  # 可留空

# 嘗試轉 float
try:
    B = float(B_val)
    Vcc = float(Vcc_val)
    X = float(X)
    Y = float(Y)
    R25_input = float(R25_val) if R25_val.strip() != "" else None
    R1_input = float(R1_val) if R1_val.strip() != "" else None
    T_input = float(Tt_val) if Tt_val.strip() != "" else None
except ValueError:
    st.error("請確認所有輸入為數字")
    st.stop()

T25 = 25 + 273.15  # 25°C in K

# 計算 Rt
def calc_Rt(R25, Tc):
    Tk = Tc + 273.15
    if therm_type == "NTC":
        return R25 * math.exp(B * (1/Tk - 1/T25))
    else:
        return R25 * math.exp(-B * (1/Tk - 1/T25))

# 反算 R25
def solve_R25(R1, Tc):
    Vout_target = Vcc*X if therm_type=="NTC" else Vcc*Y
    Rt = R1 * Vout_target / (Vcc - Vout_target)
    Tk = Tc + 273.15
    if therm_type=="NTC":
        R25 = Rt * math.exp(-B * (1/Tk - 1/T25))
    else:
        R25 = Rt * math.exp(B * (1/Tk - 1/T25))
    return R25, Rt, Vout_target

# 反算 R1
def solve_R1(R25, Tc):
    Rt = calc_Rt(R25, Tc)
    Vout_target = Vcc*X if therm_type=="NTC" else Vcc*Y
    R1 = Rt * (Vcc - Vout_target) / Vout_target
    return R1, Rt, Vout_target

# 反算目標溫度
def solve_Tt(R25, R1):
    Vout_target = Vcc*X if therm_type=="NTC" else Vcc*Y
    Rt = R1 * Vout_target / (Vcc - Vout_target)
    if therm_type=="NTC":
        invT = 1/T25 + (1/B) * math.log(Rt/R25)
    else:
        invT = 1/T25 - (1/B) * math.log(Rt/R25)
    Tk = 1/invT
    Tc = Tk - 273.15
    return Tc, Rt, Vout_target

# 判斷輸入組合
filled = [v is not None for v in [R1_input, T_input, R25_input]]
if sum(filled) != 2:
    st.info("請輸入 R1、R25、目標溫度中的任意兩個，程式將計算第三個。")
else:
    try:
        # 初始化結果區塊
        R1_info = ""
        RtR25_info = ""
        Vout_info = ""
        header = ""

        if R1_input is not None and T_input is not None:
            # 已知 R1 + Tt → 求 R25
            R25, Rt, Vout = solve_R25(R1_input, T_input)
            R1_calc = R1_input
        elif R25_input is not None and T_input is not None:
            # 已知 R25 + Tt → 求 R1
            R1_calc, Rt, Vout = solve_R1(R25_input, T_input)
        elif R25_input is not None and R1_input is not None:
            # 已知 R25 + R1 → 求 Tt
            Tt, Rt, Vout = solve_Tt(R25_input, R1_input)
            header = f"目標溫度 ≈ {Tt:.2f} °C"
            R1_calc = R1_input
        else:
            st.error("輸入解析失敗")
            st.stop()

        # 計算功率
        I = Vcc / (R1_calc + Rt)
        P_R1 = I**2 * R1_calc
        P_Rt = I**2 * Rt

        # 組合結果
        R1_info = f"R1 ≈ {R1_calc:.2f} Ω\nP_R1 ≈ {P_R1:.4f} W"
        RtR25_info = f"熱敏電阻 Rt ≈ {Rt:.2f} Ω\nR25 ≈ {R25_input if R25_input is not None else R25:.2f} Ω\nP_熱敏電阻 ≈ {P_Rt:.4f} W"
        Vout_info = f"臨界電壓 Vout ≈ {Vout:.3f} V"

        # 顯示結果
        if header != "":
            st.subheader(header)
        # R1 資訊
        st.text(R1_info)
        # 熱敏電阻資訊（Rt + R25）
        st.text(RtR25_info)
        # 臨界電壓
        st.text(Vout_info)

    except Exception as e:
        st.error(f"計算錯誤: {e}")
