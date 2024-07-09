#!/bin/bash
pip install streamlit pandas openai python-dotenv
streamlit run productdeployment.py --server.port 80
