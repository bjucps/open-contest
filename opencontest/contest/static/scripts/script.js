var MESSAGE_CHECK_SECS = 30  // check for messages every __ seconds

/*--------------------------------------------------------------------------------------------------
General page code
--------------------------------------------------------------------------------------------------*/
    // Convert date string to Date object
    function parseDateTime(strDate, strTime) {
        var date = new Date(`${strDate}T${strTime}Z`);
        return date.getTime() + (date.getTimezoneOffset() * 60000);
    }

    // Convert Date object to string with date portion
    function formatDate(date) {
        return `${date.getFullYear()}-${fix(date.getMonth() + 1)}-${fix(date.getDate())}`;
    }

    // Convert Date object to string with time portion
    function formatTime(time) {
        return `${fix(time.getHours())}:${fix(time.getMinutes())}`
    }

    // HTML Encode 
    function htmlEncode(msg) {
        if (!msg)
            msg = ''
        return msg.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    }

    // from https://www.quirksmode.org/js/cookies.html
    function readCookie(name) {
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for(var i=0;i < ca.length;i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1,c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
        }
        return null;
    }    

    function setupHeaderDiv() {
        $("div.header").click(_ => {
            window.location = "/";
        });
    }

    var userLoginTime = 0;
    var userType = "";
    var user = "";
    function setupMenu() {
        if (document.cookie) {
            userLoginTime = Number(readCookie("userLoginTime"));
            userType = readCookie("userType");
            user = readCookie("user");
        }
        $("div.menu-item").each(function() {
            var perms = $(this).attr("role");
            if (perms == "any" || perms == userType) {
                $(this).css("display", "inline-block");
            }
        });
    }

    $(document).ready(function() {
        var pageName = $("#pageId").val();
        setupMenu();
        setupLoginButton();
        setupHeaderDiv();
        fixFormatting();
        showCountdown();
        displayRemainingTime();
        displayIncomingMessages();
        if ($("#ace-editor").length > 0) {
            setupAceEditor();
            // Comment out the following to disable draggable info blocks:
            // setupSortability();
        }
        if (pageName == "Users") {
            displayExistingUsers();
            setupUserButtons();
        } else if (pageName == "Contests") {
            displayExistingContests();
            setupContestButton();
        } else if (pageName == "Contest") {
            setupContestPage();
        } else if (pageName == "Problem") {
            setupProblemPage();
        }
        $(".result-tabs").tabs();
        // $(".tablesorter").tablesorter();
        var props = {
            sort: true,
            filters_row_index:1,
            remember_grid_values: true,
            alternate_rows: true,
            base_path: '/static/lib/tablefilter/',
            custom_slc_options: {
                cols:[],
                texts: [],
                values: [],
                sorts: [],
            }
        };
        if ($("#submissions").length) {
            var tf = new TableFilter("submissions", props);
            tf.init();
            tf.setFilterValue(5, "Review");
            tf.filter();
        }
    });
/*--------------------------------------------------------------------------------------------------
Problem page
--------------------------------------------------------------------------------------------------*/
    function showCountdown() {
        if ($(".countdown").length == 0) {
            return;
        }
        var contestStart = parseInt($(".countdown").text() || "0");
        var updateTime = _ => {
            var diff = Math.floor((contestStart - new Date().getTime()) / 1000);
            if (diff <= 0) {
                window.location.reload();
            }
            var seconds = diff % 60;
            var minutes = Math.floor(diff / 60) % 60;
            var hours = Math.floor(diff / 3600);
            if (seconds < 10) seconds = "0" + seconds;
            if (minutes < 10) minutes = "0" + minutes;
            $(".countdown").text(`${hours}:${minutes}:${seconds}`)
        };
        window.setInterval(updateTime, 1000);
        updateTime();
    }

    var languages;
    var language;

    async function getLanguages() {
        return new Promise((res, rej) => {
            if (localStorage.languages != undefined) {
                languages = JSON.parse(localStorage.languages);
                res();
            } else {
                $.get("/static/languages.json", {}, data => {
                    localStorage.languages = JSON.stringify(data);
                    languages = JSON.parse(localStorage.languages);
                    res();
                });
            }
        });
    }

    function setupLanguageDropdown() {
        for (var language in languages) {
            $("select.language-picker").append(`<option value="${language}">${languages[language].name}</option>`);
        }
        if (localStorage.language != undefined) {
            $("select.language-picker").val(localStorage.language);
        }
    }

    async function getLanguageDefault(language) {
        return new Promise((res, rej) => {
            if (localStorage[language] != undefined) {
                res(localStorage[language]);
            } else {
                $.get("/static/examples/" + languages[language].example, {}, data => {
                    localStorage[language] = data;
                    res(data);
                });
            }
        });
    }

    function createResultsCard() {
        if ($(".card.results").length == 0) {
            $(".main-content").append(`<div class="results card">
                <div class="card-header">
                    <h2 class="card-title">Results</h2>
                </div>
                <div class="card-contents">
                </div>
            </div>`);
        }
        $(".results.card .card-contents").html(`<div class="results-pending"><i class="fa fa-spinner fa-pulse fa-3x fa-fw"></i></div>`);
    }

    var icons = {
        "ok": "check",
        "extra_output": "times",
        "incomplete_output": "times",
        "wrong_answer": "times",
        "tle": "clock",
        "runtime_error": "exclamation-triangle",
        "presentation_error": "times",
        "reject" : "times",
        "internal_error": "exclamation-triangle",
        "pending": "sync",
        "pending_review": "sync",
    };
    var verdict_name = {
        "ok": "Accepted",
        "extra_output": "Extra Output",
        "incomplete_output": "Incomplete Output",
        "wrong_answer": "Wrong Answer",
        "tle": "Time Limit Exceeded",
        "runtime_error": "Runtime Error",
        "presentation_error": "Presentation Error",
        "reject": "Submission Rejected",
        "internal_error": "Internal Error",
        "pending": "Executing ...",
        "pending_review": "Pending Review",
    };

    function encodeText(msg) {
        return htmlEncode(msg).replace(/\n/g, "<br/>").replace(/ /g, "&nbsp;")
    }

    function showResults(sub) {
        if (sub.result == "internal_error") {
            $(".results.card .card-contents").html(`
                <h3>Unexpected Error</h3>
                <p>${sub.error}</p>
            `);
        } else if (sub.result == "compile_error") {
            $(".results.card .card-contents").html(`
                <h3>Compile Error</h3>
                <code>${encodeText(sub.compile)}</code>
            `);
        } else if (sub.type == "test" || sub.type == "custom") {
            var tabs = "";
            var results = "";
            var samples = sub.results.length;
            if(sub.type == "custom"){
                samples = 1;
            }
            for (var i = 0; i < samples; i ++) {
                var res = sub.results[i];
                var icon = icons[res];
                var tabLabel = (sub.type == "custom") ? "Custom" : `Test #${i}`
                tabs += `<li><a href="#tabs-${i}"><i class="fa fa-${icon}" title="${verdict_name[res]}"></i> ${tabLabel}</a></li>`;
                
                var input = sub.inputs[i];
                var output = sub.outputs[i];
                var error = sub.errors[i];
                var answer = (sub.type == "custom") ? "N/A" : sub.answers[i];
                var errorStr = `<div class="col-12">
                    <h4>Stderr Output</h4>
                    <code>${encodeText(error)}</code>
                </div>`;
                if (!error) {
                    errorStr = "";
                }

                results += `<div id="tabs-${i}">
                    <div class="row">
                        <div class="col-12">
                            <h4>Input</h4>
                            <code>${encodeText(input)}</code>
                        </div>
                        <div class="col-6">
                            <h4>Your Output</h4>
                            <code>${encodeText(output)}</code>
                        </div>
                        <div class="col-6">
                            <h4>Correct Answer</h4>
                            <code>${encodeText(answer)}</code>
                        </div>
                        ${errorStr}
                    </div>
                </div>`;
                
            }
            $(".results.card .card-contents").html(`<div id="result-tabs">
                <ul>
                    ${tabs}
                </ul>
                ${results}
            </div>`);
            $("#result-tabs").tabs();
        } else {
            var results = "";
            for (var i = 0; i < sub.results.length; i ++) {
                var res = sub.results[i];
                var icon = icons[res];
                results += `<div class="col-2"><i class="fa fa-${icon}" title="${verdict_name[res]}"></i> Case #${i}</div>`;
            }
            $(".results.card .card-contents").html(`<div class="pad">
                <h2>Result: ${verdict_name[sub.result]}</h2>
                <div class="row">
                    ${results}
                </div>
            </div>`);
        }
        scrollTo(0,document.body.scrollHeight);
    }

    async function setupAceEditor() {
        await getLanguages();
        // Get problem ID
        var thisProblem = $("#problem-id").val();

        // Setup ACE editor
        var editor = ace.edit("ace-editor");
        editor.setShowPrintMargin(false);
        editor.setTheme("ace/theme/chrome");

        setupLanguageDropdown();

        // Change the editor when the language changes
        async function setLanguage() {
            language = $("select.language-picker").val();
            localStorage.language = language;
            editor.session.setMode("ace/mode/" + languages[language].aceName);
            if (localStorage[language + "-" + thisProblem] == undefined) {
                localStorage[language + "-" + thisProblem] = await getLanguageDefault(language);
                editor.setValue(localStorage[language + "-" + thisProblem]);
            } else {
                editor.setValue(localStorage[language + "-" + thisProblem]);
            }
        }
        setLanguage();
        $("select.language-picker").change(setLanguage);

        // Save the editor contents to local storage when the editor changes
        editor.session.on('change', delta => {
            localStorage[language + "-" + thisProblem] = editor.getValue();
        });

        function disableButtons() {
            $(".submit-problem").attr("disabled", true);
            $(".submit-problem").addClass("button-gray");
            $(".test-samples").attr("disabled", true);
            $(".test-samples").addClass("button-gray");            
        }

        function enableButtons() {
            $(".submit-problem").attr("disabled", false);
            $(".submit-problem").removeClass("button-gray");
            $(".test-samples").attr("disabled", false);
            $(".test-samples").removeClass("button-gray");
        }

        // submit or test code
        $("button.test-samples, button.submit-problem").click(function() {
            createResultsCard();
            var code = editor.getValue();
            var input = $("#custom-input").val();

            var type = $(this).text() == "Submit Code" ? "submit" :
                        $("#use-custom-input")[0].checked ? "custom" :
                            "test";

            disableButtons();
            $.post("/submit", {
                problem: thisProblem, language: language, code: code, type: type, input: input
            }).done(function(results) {
                enableButtons();
                showResults(results);
            }).fail(function() {
                enableButtons();
                showResults({ result: 'internal_error', error: 'Unexpected problem testing your submission. Please notify the contest administrator.' });
            });
        });

        $("#use-custom-input").change(function() {
            $(".blk-custom-input").css('display', this.checked ? 'block' : 'none');
        })

        $(".blk-custom-input").css('display', 'none');
    }

    // Allow problem info blocks to be sorted
    function setupSortability() {
        var thisProblem = $("#problem-id").val();
        if (localStorage["sort-" + thisProblem] != undefined) {
            var order = JSON.parse(localStorage["sort-" + thisProblem]);
            for (var i of [0,1,2,3,4]) {
                var cls = order[i];
                $("div.problem-description").append($("div.problem-description div." + cls))
            }
        }
        $("div.problem-description").sortable({
            placeholder: "ui-state-highlight",
            forcePlaceholderSize: true,
            stop: (event, ui) => {
                var indices = {};
                for (var cls of ["stmt", "inp", "outp", "constraints", "samples"]) {
                    var index = $("div.problem-description > div." + cls).index();
                    indices[index] = cls;
                }
                localStorage["sort-" + thisProblem] = JSON.stringify(indices);
            }
        });
        $("div.problem-description").disableSelection();
    }

/*--------------------------------------------------------------------------------------------------
Login page
--------------------------------------------------------------------------------------------------*/
    function login() {
        // Clear localStorage
        for (var key of Object.keys(localStorage)) {
            delete localStorage[key];
        }

        var username = $("input[name=username]").val();
        var password = $("input[name=password]").val();
        $.post("/login", {username: username, password: password}, data => {
            if (data == "ok") {
                window.location = "/problems";
            } else {
                alert(data);
            }
        });
    }

    function loginIfEnter(event) {
        if (event.keyCode == 13) {
            // the user pressed the enter key
            login();
        }
    }

    function setupLoginButton() {
        if ($("input[name=username]").length > 0) {
            $(".login-button").click(login);
            $("input[name=username]").focus();
            $("input[name=username]").keypress(loginIfEnter);
            $("input[name=password]").keypress(loginIfEnter);
        }
    }

/*--------------------------------------------------------------------------------------------------
Users page
--------------------------------------------------------------------------------------------------*/
    function deleteUser(username) {
        if (confirm(`Are you sure you want to delete ${username}?`)) {
            $.post("/deleteUser", {username: username}, data => {
                if (data == "ok") {
                    window.location.reload();
                }
            });
        }
    }

    function createUser(type) {
        var username = prompt("New User's Name")
        var fullname = prompt("New User's Fullname")

        if (username) {
            $.post("/createUser", {type: type, username: username, fullname: fullname}, password => {
                window.location.reload();
            });
        }
    }

/*--------------------------------------------------------------------------------------------------
Contests page
--------------------------------------------------------------------------------------------------*/
    function deleteContest(id) {
        var name = $(`.card.${id} .card-title`).text();
        if (confirm(`Are you sure you want to delete ${name}?`)) {
            $.post("/deleteContest", {id: id}, data => {
                if (data == "ok") {
                    window.location.reload();
                }
            });
        }
    }

/*--------------------------------------------------------------------------------------------------
Contest page
--------------------------------------------------------------------------------------------------*/
    function editContest(newProblem=undefined) {
        var id = $("#contest-id").val();
        var name = $("#contest-name").val();
        var startDate = $("#contest-start-date").val();
        var startTime = $("#contest-start-time").val();
        var endDate = $("#contest-end-date").val();
        var endTime = $("#contest-end-time").val();
        var scoreboardOffTime = $("#scoreboard-off-time").val();
        var showProblInfoBlocks = $("#show-problem-info-blocks").val();
        var displayFullname = $("#contest-display-fullname").val();

        var tieBreaker = $("#scoreboard-tie-breaker").val();

        var start = parseDateTime(startDate, startTime);
        var end = parseDateTime(endDate, endTime);
        var endScoreboard = parseDateTime(endDate, scoreboardOffTime);

        if (end <= start) {
            alert("The end of the contest must be after the start.");
            return;
        }

        if (!(start < endScoreboard && endScoreboard <= end)) {
            alert("The scoreboard off time must be between the start and end time.");
            return;
        }

        var problems = [];
        var uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        $(".problem-cards .card").each((_, card) => {
            var prob = "";
            for (var cls of $(card).attr("class").split(" ")) {
                if (uuid.test(cls)) {
                    prob = cls;
                    break;
                }
            }
            problems.push(prob);
        });
        if (newProblem != undefined) {
            problems.push(newProblem);
        }

        $.post("/editContest", {id: id, name: name, start: start, end: end, scoreboardOff: endScoreboard, 
            showProblInfoBlocks: showProblInfoBlocks, tieBreaker: tieBreaker.toString(),
            displayFullname: displayFullname.toString(),
            problems: JSON.stringify(problems)}, id => {
            if (window.location.pathname == "/contests/new") {
                window.location = `/contests/${id}`;
            } else {
                window.location.reload()
            }
        });
    }

    function fix(num) {
        // Fix to 2 decimals
        if (num < 10) {
            return "0" + num;
        }
        return num;
    }

    var problemsHere = {};
    function setupContestPage() {
        var start = new Date(parseInt($("#start").val()));
        $("#contest-start-date").val(formatDate(start));
        $("#contest-start-time").val(formatTime(start));
        
        var end = new Date(parseInt($("#end").val()));
        $("#contest-end-date").val(formatDate(end));
        $("#contest-end-time").val(formatTime(end));

        var endScoreboard = new Date(parseInt($("#scoreboardOff").val()));
        $("#scoreboard-off-time").val(formatTime(endScoreboard));

        $("div.problem-cards").sortable({
            placeholder: "ui-state-highlight",
            forcePlaceholderSize: true,
            stop: _ => editContest()
        });
    }

    function deleteContestProblem(id) {
        $(`.card.${id}`).remove();
        editContest();
    }

    function chooseProblemDialog() {
        $("div.modal").modal();
    }

    function chooseProblem() {
        if ($("select.problem-choice").val() != "-") {
            var problem = $("select.problem-choice").val();
            editContest(problem);
        }
    }

/*--------------------------------------------------------------------------------------------------
Problems page
--------------------------------------------------------------------------------------------------*/
    function deleteProblem(id) {
        var title = $(`div.card.${id}`).find(".card-title").text();
        if (!confirm(`Are you sure you want to delete ${title}?`)) {
            return;
        }
        $.post("/deleteProblem", {id: id}, data => {
            if (data == "ok") {
                window.location.reload();
            }
        });
    }

/*--------------------------------------------------------------------------------------------------
Problem page
--------------------------------------------------------------------------------------------------*/
    function createTestDataDialog() {
        $(".create-test-data").modal();
    }

    function createTestData() {
        var input = $(".test-data-input").val();
        var output = $(".test-data-output").val();
        editProblem({input: input, output: output});
    }

    var handlingClick = false;
    function editProblem(newTest=undefined) {
        // Eliminate double-click problem
        if (handlingClick) {
            // User has already clicked the button recently and the request isn't done
            return;
        }
        handlingClick = true;

        var id = $("#prob-id").val();
        var problem = {id: id};
        problem.title       = $("#problem-title").val();
        problem.timelimit   = $("#problem-timelimit").val();
        problem.description = $("#problem-description").val();        
        problem.statement   = mdEditors[0].value();
        problem.input       = mdEditors[1].value();
        problem.output      = mdEditors[2].value();
        problem.constraints = mdEditors[3].value();
        
        problem.samples     = $("#problem-samples").val();
        testData = [];
        $(".test-data-cards .card").each((_, card) => {
            var input = $(card).find("code:eq(0)")[0].innerText.replace('\xa0', ' ');
            var output = $(card).find("code:eq(1)")[0].innerText.replace('\xa0', ' ');
            console.log('output:', output);
            testData.push({input: input, output: output});
        });
        if (newTest != undefined) {
            testData.push(newTest);
        }
        problem.testData = JSON.stringify(testData);
        
        if (problem.samples > testData.length) {
            alert("You have set the number of samples beyond the number of tests available.");
            return;
        }

        $.post("/editProblem", problem, id => {
            if (window.location.pathname == "/problems/new") {
                window.location = `/problems/${id}/edit`;
            } else {
                window.location.reload();
            }
        });
        return false;
    }

    /**
     * Opens and Initializes a dialog box confirming if the admin wants to delete a test cases
     * @param   {Number} dataNum    Test case number to delete
     */
    function deleteTestDataDialog(dataNum) {

        // Change the question to ask about the relevant Test Case number
        $(".delete-test-data-question").html(`Are you sure you want to delete Test Case #${dataNum}?`);

        // Set the test data id variable appropriately
        $(".delete-test-data-id").html(dataNum);

        // Open the modal
        $(".delete-test-data").modal();
    }

    function deleteTestData() {
        if ($(".test-data-cards .card").length <= $("#problem-samples").val()) {
            alert("Deleting this item would make the number of sample cases invalid.");
            return;
        }
        let dataNum = $(".delete-test-data-id").html();
        $(`.test-data-cards .card:eq(${dataNum})`).remove();
        editProblem();
    }
    
        /**
     * Opens and Initializes a dialog box for editing test cases
     * @param   {Number} dataNum    Test case number to edit
     */
    function editTestDataDialog(dataNum) {

        // Get test case data from test case cards
        let input = $(`.test-data-cards .card:eq(${dataNum}) code:eq(0)`).text();
        let output = $(`.test-data-cards .card:eq(${dataNum}) code:eq(1)`).text();

        // Load data into dialog
        $(".edit-test-input").val(input);
        $(".edit-test-output").val(output);

        // Change the title of the card to match case number
        $(".edit-test-data .modal-title").html(`Editing Test Case #${dataNum}`);
        $(".current-test-data-id").html(dataNum);

        // Load the 
        $(`.edit-test-data`).modal();
    }

    /**
     * Saves test cases currently in the editor
     */
    function editTestData() {

        // Get the test case id
        dataNum = $(".current-test-data-id").html();

        // Get the new input and output
        let input = $(".edit-test-input").val();
        let output = $(".edit-test-output").val();

        // Load the new input and output into the test case cards
        $(`.test-data-cards .card:eq(${dataNum}) code:eq(0)`).text(input);
        $(`.test-data-cards .card:eq(${dataNum}) code:eq(1)`).text(output);

        // Upload data to server
        editProblem();
    }
    
    var mdEditors = [];
    function setupProblemPage() {
        $(".rich-text textarea").each((_, elem) => {
            mdEditors.push(new SimpleMDE({ element: elem }));
        });
        $("div.test-data-cards").sortable({
            placeholder: "ui-state-highlight",
            forcePlaceholderSize: true,
            stop: _ => editProblem()
        });
    }

/*--------------------------------------------------------------------------------------------------
General
--------------------------------------------------------------------------------------------------*/
    async function fixFormatting() {
        $(".time-format").each((_, span) => {
            var timestamp = $(span).text();
            if ($.isNumeric(timestamp)) {
                var d = new Date(parseInt(timestamp));
                $(span).text(d.toLocaleTimeString());
            }
        });
        await getLanguages();
        $("span.language-format").each((_, span) => {
            var lang = $(span).text();
            $(span).text(languages[lang].name);
        });
        $("span.result-format").each((_, span) => {
            var result = $(span).text();
            $(span).text(verdict_name[result]);
        });

        $("span.login-user").each((_, span) => {
            var user = readCookie("user");
            var dashPos = user.indexOf('-')
            if (dashPos > 0) {
                user = user.substring(0, dashPos);
            }
            if (user) {
                $(span).text('User: ' + user);
            }
        });
        $("span.time-remaining").each((_, span) => {
            var remaining = parseInt($(span).text() / 60);
            if (remaining) {
                window.setTimeout( () => {
                    remaining--;
                    $(span).text("Time remaining:" + new Date(remaining * 60 * 1000).toLocaleTimeString('it-IT'));
                }, 1000)
            }
        });

    }

    var remainingTime;

    function displayRemainingTime() {
        if (!remainingTime) {
            remainingTime = parseInt($('span.time-remaining').attr('data_timeremaining'));
        }
        if (remainingTime && remainingTime > 0) {
            remainingTime--;
            var dateObj = new Date(remainingTime * 1000);
            var hours = dateObj.getUTCHours();
            var minutes = dateObj.getUTCMinutes();
            var seconds = dateObj.getSeconds();

            var timeString = hours.toString().padStart(2, '0') + ':' + 
                minutes.toString().padStart(2, '0') + ':' + 
                seconds.toString().padStart(2, '0');
            $('span.time-remaining').text("Time remaining: " + timeString);
            window.setTimeout(displayRemainingTime, 1000)
        }
    }

/*--------------------------------------------------------------------------------------------------
Messages Page
--------------------------------------------------------------------------------------------------*/
    function createMessage() {
        $("div.modal").modal();
    }

    function sendMessage() {
        var text = $("textarea.message").val();
        var recipient = $("select.recipient").val();
        var replyTo = $("#replyTo").val();
        $.post("/sendMessage", {to: recipient, message: text, replyTo: replyTo}, result => {
            if (result == "ok") {
                $("div.modal").modal("hide");
                window.location.reload()
            } else {
                alert(result);
            }
        });
    }

    function reply(user, replyToMsgId) {
        $("select.recipient").val(user);
        $("#replyTo").val(replyToMsgId);
        createMessage();
        $("textarea.message").focus();
    }

    function showIncomingMessage(msg) {
        var body = msg.message;
        if (msg.general) {
            body = "General Announcement: " + body
        } else if (msg.admin) {
            // message sent to admin by participant
            body = "From " + msg.from.username + ": " + body
        } else {
            body = "From judges: " + body
        }
        $("div.message-alerts").append(`<div class="alert alert-warning alert-dismissible fade show" role="alert">
            ${body}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>`);
    }

    var lastChecked = 0;
    var seenMessages = JSON.parse(localStorage.seenMessages || "{}");
    function displayIncomingMessages() {
        $.post("/getMessages", {timestamp: lastChecked}, messages => {
            lastChecked = messages.timestamp
            for (message of messages.messages) {
                if (message.id in seenMessages || message.from.id == user || message.timestamp < userLoginTime) {
                    continue;
                }
                showIncomingMessage(message);
                seenMessages[message.id] = message;
            }
            localStorage.seenMessages = JSON.stringify(seenMessages);
        });
        window.setTimeout(displayIncomingMessages, MESSAGE_CHECK_SECS * 1000);
    }

/*--------------------------------------------------------------------------------------------------
Judging Page
--------------------------------------------------------------------------------------------------*/
    // Page initialization
    $(function() {
        // Handle change event for result-choice dropdown in submission popup
        $('.modal-dialog').on('change', '.result-choice', function() {
            $(".status-choice").val("Judged");
        });

        $('.submit-row').click(function() {
            if ($(this).text().indexOf("Executing") == -1) {
                submissionPopup($(this).attr('id'));
            }
        });

    })

    function changeSubmissionResult(id, version) {
        var result = $(`.result-choice.${id}`).val();
        var status = $(`.status-choice.${id}`).val();
        $.post("/changeResult", {id: id, result: result, status: status, version: version}, result => {
            if (result == "ok") {
                window.location.reload();
            } else {
                alert(result);
            }
        })
    }

    function submissionPopup(id, force) {
        var version = $(`#${id}-version`).text();
        var url = `/judgeSubmission/${id}` + (force ? "/force" : "");
        $.post(url, {version: version}, data => {
            if (data.startsWith("CONFLICT") && !force) {
                var otherJudge = data.slice(data.indexOf(":")+1, data.length);
                if (window.confirm(`${otherJudge} is already reviewing this submission. Do you want to override with your review?`))
                    submissionPopup(id, true);
            }
            else if (data.startsWith("CHANGES")) {
                window.alert(`The state of the record you are about to access has changed. The window will reload to retrieve the new changes.`);
                window.location.reload();
            }
            else {
                let activeTab;

                $(".modal-dialog").html(data);
                $(".result-tabs").tabs();
                // Select the first tab with an error report
                $('.result-tabs a').each( (i, itm) => {
                    if ($('i', itm).attr('title') != 'Accepted' && activeTab == undefined) {
                        activeTab = i;
                    }
                });
                if (activeTab != undefined) {
                    $('.result-tabs').tabs( 'option', 'active', activeTab);
                }
                fixFormatting();

                $(".modal").modal().click(() => $.post("/judgeSubmissionClose", {id: id, version: $("#version").val()} ));
            }
        });
    }

    function submissionPopupContestant(id) {
        $.post(`/contestantSubmission/${id}`, {}, data => {
            $(".modal-dialog").html(data);
            $(".result-tabs").tabs();
            fixFormatting();
            $(".modal").modal();
        });
    }

    function rejudge(id) {
        $(".rejudge").attr("disabled", true);
        $(".rejudge").addClass("button-gray");

        $.post("/rejudge", {id: id}, data => {
            $(".rejudge").attr("disabled", false);
            $(".rejudge").removeClass("button-gray");
            alert(`New Result: ${verdict_name[data]}`);
            window.location.reload();
        });
    }
  
    function rejudgeAll(id)
    {
        if (!confirm('This will invoke the auto judge on all submissions for this problem. Are you sure you wish to continue?'))
            return;

        $.post("/rejudgeAll", {id:id}, data =>{
            alert(data);
        });
    }

    

    function download(id) {
        $(".rejudge").attr("disabled", true);
        $(".rejudge").addClass("button-gray");

        $.post("/download", {id: id}, data => {
            $(".rejudge").attr("disabled", false);
            $(".rejudge").removeClass("button-gray");
            file = JSON.parse(data)
            jQuery.each(file, (name, value) => {
                byteCharacters = atob(value)
                const byteNumbers = new Array(byteCharacters.length)
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i)
                }
                const byteArray = new Uint8Array(byteNumbers);
                saveAs(new Blob([byteArray], {type: "application/zip"}, name))
            })
            
        });
    }