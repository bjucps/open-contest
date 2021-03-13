# User Manual

## Contest Setup

To setup OpenContest, you begin by creating problems (see "How to Create a Problem" below).
Then, you create one or more contests and configure them to use the problems you have created.

### How to Create a Problem
To create a problem, follow these steps:
1. Login to OpenContest with the username and password provided when you started the server.
2. Choose *Setup* in the menu.
3. Choose *Problems*.
4. Click *Create Problem*.
5. Enter the details of the problem. You may use Markdown formatting for the Problem Statement, Input Format, Output Format, and Constraints.
   * **Description**: The text shown under the problem title in the list of all problems.
   * **Number of Sample Cases**: Leave this at 0 until after adding test cases. After adding test cases, set this to at least 1 to allow contestants to test solutions before submitting. 
   * **Time Limit**: The maximum cumulative CPU time that solutions are allowed to use to solve all
     of the test cases. So, if the time limit is 5, all test case runs must complete within a
     cumulative total of 5 seconds.
6. After saving the problem details, create test data.
    - Click *Create Test Data*.
    - Enter input and output data. 
    - Click *Add Test Data*. Sample data cases are shown to the contestant on the problem info screen.
7. After creating the test data, set the number of sample cases and save the problem.

### How to Create a Contest
OpenContest allows you to create multiple contests that run at different times. The most common use case for this feature is to allow for a practice round before an actual contest. To create a contest, go to Setup > Contest > Create Contest and enter the contest details. Here are some of the details:
* **Contest Info Blocks:** Set this to Off if you will distribute the contest problems on paper and
  do not want to clutter the contestant problem view with details problem descriptions, etc.
* **Show Full Name:** If On, the contestant name appears in the leaderboard reports. If Off, only the contestant username appears.
* **Sample Data Breaks Ties:** If On, two contestants who solve the same number of problems will be ranked first by the additional number of
  problems for which they solved the problem partly correct (it works for sample data but not for all official judge tests), then by penalty points.
  When this option is On, the system forces judges to review all solutions that correctly handled the sample cases but did not correctly handle
  the official judge tests.

After creating the contest, you can choose problems to go into the contest.

Before the contest begins, the home page will show a countdown to the beginning of the contest.

During the contest, the home page will show a list of problems in the contest.

After the contest ends, the final leaderboard for the most recent contest will be visible.

### How To Print a Problem
OpenContest formats problems for printing so that you can print and distribute problem statement packets to contestants. To print a problem, go to the edit page for the problem, click *View Problem*, and print the page with Ctrl+P.

### How To Print the User Login Information
From the user list page, you can print the page with Ctrl+P for a list of usernames and passwords. You can then cut the paper and deliver these sheets to the contestants.

## About Autojudging and the Judge Submissions Screen
The system automatically judges submissions as follows:

* When a contestant submits a solution, the submitted code is executed once for each test case. All test cases must complete within the configured problem time limit (see Time Limit above).
* Solutions that pass all tests are automatically accepted and do not appear in the Judge Submissions screen.
* Otherwise, the system assigns the result of the first non-correct test case as the result of the entire submission. So, if test case 0 is correct, 1 is Runtime Error, and 2 is TLE,
  the overall result is Runtime Error.
* Solutions that fail tests with only the following reasons are automatically rejected and do not appear in the Judge Submissions screen: TLE, Runtime Error. However,
  see "Sample Data Breaks Ties" above for special handling when that option is on.
* Solutions that fail tests for other reasons appear in the Judge Submissions Screen for review by judges.

## System Configuration
Configuration parameters are defined in open-contest.config. To adjust these parameters, copy open-contest.config into your
database folder and edit it.

## New Relic Monitoring
OpenContest has a New Relic integration for monitoring the server performance. To enable it, 

1. Copy **newrelic.ini.template** into your database folder and edit it to insert your license key.
2. Copy open-contest.config into your database folder and edit it to set **OC_MONITORING=1**
3. Start the server. You should see monitoring available in the New Relic console at https://one.newrelic.com/.
