# Machine Learning Model Benchmark Summary

- **Evaluation Test Set Size:** 130 complaints
- **Evaluation Type:** Held-out Stratified Test Set
- **Metrics Source:** Actual scikit-learn evaluations on real text features (Zero fabricated values)

---

## 1. Overall Performance Comparison

| Model Architecture | Target Attribute | Accuracy | Precision (Macro) | Recall (Macro) | F1-Score (Macro) | F1-Score (Weighted) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline LogisticRegression** | Department | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **Baseline LogisticRegression** | Category | 26.2% | 27.0% | 26.9% | 24.4% | 24.9% |
| **Baseline LogisticRegression** | Priority | 39.2% | 39.6% | 39.4% | 39.2% | 39.2% |
| **Baseline LogisticRegression** | Sentiment | 46.9% | 44.9% | 46.5% | 42.1% | 49.6% |
| **Naive Bayes** | Department | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **Naive Bayes** | Category | 24.6% | 20.2% | 25.6% | 20.9% | 21.4% |
| **Naive Bayes** | Priority | 40.0% | 40.3% | 40.2% | 39.9% | 39.9% |
| **Naive Bayes** | Sentiment | 47.7% | 41.1% | 42.3% | 40.4% | 49.9% |

---

## 2. Confusion Matrices (Baseline: TF-IDF + Logistic Regression)

### Target: DEPARTMENT

| Actual \ Predicted | Customer Support | Finance | IT | Logistics | Security |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Customer Support** | 26 | 0 | 0 | 0 | 0 |
| **Finance** | 0 | 26 | 0 | 0 | 0 |
| **IT** | 0 | 0 | 24 | 0 | 0 |
| **Logistics** | 0 | 0 | 0 | 26 | 0 |
| **Security** | 0 | 0 | 0 | 0 | 28 |

### Target: CATEGORY

| Actual \ Predicted | Access & Permissions | Account Management | Billing | Cancellation | Damaged Package | Data Exposure | Delivery Delay | General Inquiry | Hardware | Invoices | Missing Items | Network & Connectivity | Onboarding | Payments | Phishing | Policy Violation | Refunds | Returns & Pickup | Software Crash | Unauthorized Access |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Access & Permissions** | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Account Management** | 0 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Billing** | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 5 | 0 | 0 | 0 |
| **Cancellation** | 0 | 2 | 0 | 3 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Damaged Package** | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| **Data Exposure** | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 4 |
| **Delivery Delay** | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| **General Inquiry** | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Hardware** | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| **Invoices** | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 3 | 0 | 0 | 0 |
| **Missing Items** | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| **Network & Connectivity** | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| **Onboarding** | 0 | 4 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Payments** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| **Phishing** | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **Policy Violation** | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 1 |
| **Refunds** | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 3 | 0 | 0 | 0 |
| **Returns & Pickup** | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Software Crash** | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| **Unauthorized Access** | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3 | 0 | 0 | 0 | 2 |

### Target: PRIORITY

| Actual \ Predicted | P1 | P2 | P3 | P4 |
| :--- | :---: | :---: | :---: | :---: |
| **P1** | 14 | 8 | 4 | 9 |
| **P2** | 11 | 11 | 7 | 5 |
| **P3** | 4 | 2 | 12 | 12 |
| **P4** | 2 | 6 | 9 | 14 |

### Target: SENTIMENT

| Actual \ Predicted | Negative | Neutral | Positive |
| :--- | :---: | :---: | :---: |
| **Negative** | 38 | 17 | 25 |
| **Neutral** | 5 | 7 | 13 |
| **Positive** | 4 | 5 | 16 |

