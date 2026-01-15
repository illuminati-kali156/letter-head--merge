# ... (previous code inside the button click) ...
        
            if err:
                status.update(label="Failed", state="error")
                st.error(f"Error: {err}")
            else:
                status.update(label="Complete!", state="complete", expanded=False)
                st.balloons()
                
                st.success("✅ Success! Files Ready.")
                
                d1, d2 = st.columns(2)
                with d1:
                    with open(pdf, "rb") as f:
                        st.download_button("⬇ Download PDF", f, "Merged_Doc.pdf", "application/pdf", use_container_width=True)
                with d2:
                    with open(docx, "rb") as f:
                        st.download_button("⬇ Download Word", f, "Merged_Doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                # Final Cleanup
                os.remove(pdf)
                os.remove(docx)
    else:
        # <--- THIS WAS THE PROBLEM AREA
        st.toast("⚠️ Please upload both files! (दोन्ही फाइल अपलोड करा)", icon="⚠️")
