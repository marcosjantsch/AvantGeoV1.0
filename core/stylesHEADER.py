import streamlit as st


def apply_stylesHEADER():
    st.markdown(
        """
        <style>
        .avant-header-spacer{
            height: 86px;
        }

        .avant-header-wrap{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 999;
            padding: 10px 18px 8px 18px;
            background: rgba(8, 12, 24, 0.78);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255,255,255,0.08);
            animation: avantHeaderFadeIn 0.35s ease-out;
        }

        .avant-header-grid{
            display: grid;
            grid-template-columns: 1fr minmax(280px, 520px) 1fr;
            align-items: center;
            gap: 12px;
            width: 100%;
        }

        .avant-header-left{
            display: flex;
            align-items: center;
            gap: 14px;
            min-width: 0;
        }

        .avant-header-logo{
            height: 46px;
            width: auto;
        }

        .avant-header-brand{
            font-size: 25px;
            font-weight: 700;
        }

        .avant-header-version{
            font-size: 11px;
            opacity: 0.65;
        }

        .avant-header-center{
            display: flex;
            justify-content: center;
        }

        .avant-header-subtitle{
            font-size: 22px;
            font-weight: 600;
            opacity: 0.95;
        }

        .avant-header-right{
            display: flex;
            justify-content: flex-end;
            gap: 8px;
        }

        .avant-header-pill{
            padding: 5px 10px;
            border-radius: 999px;
            font-size: 11px;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.06);
        }

        @keyframes avantHeaderFadeIn{
            from{
                opacity: 0;
                transform: translateY(-8px);
            }
            to{
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 900px){
            .avant-header-grid{
                grid-template-columns: 1fr;
                text-align: center;
            }

            .avant-header-right{
                justify-content: center;
            }

            .avant-header-spacer{
                height: 130px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )