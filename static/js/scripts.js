// .static/js/scripts.js

document.addEventListener("DOMContentLoaded", function () {
    // Profile form validation
    const profileForm = document.querySelector("form.profile-form");

    if (profileForm) {
        profileForm.addEventListener("submit", function (event) {
            let valid = true;
            const name = document.getElementById("name");
            const graduationYear = document.getElementById("graduation_year");
            const industry = document.getElementById("industry");
            const contactDetails = document.getElementById("contact_details");

            // Simple validation checks
            if (!name.value.trim()) {
                valid = false;
                alert("Name is required.");
                name.focus();
            } else if (!graduationYear.value.trim() || isNaN(graduationYear.value) || graduationYear.value < 1900 || graduationYear.value > new Date().getFullYear()) {
                valid = false;
                alert("Please enter a valid graduation year.");
                graduationYear.focus();
            } else if (!industry.value.trim()) {
                valid = false;
                alert("Industry is required.");
                industry.focus();
            } else if (!contactDetails.value.trim()) {
                valid = false;
                alert("Contact details are required.");
                contactDetails.focus();
            }

            if (!valid) {
                event.preventDefault(); // Prevent form submission if validation fails
            }
        });
    }

    // Event form validation
    const eventForm = document.querySelector("form.event-form");

    if (eventForm) {
        eventForm.addEventListener("submit", function (event) {
            let valid = true;
            const title = document.getElementById("title");
            const date = document.getElementById("date");
            const location = document.getElementById("location");
            const description = document.getElementById("description");

            // Simple validation checks
            if (!title.value.trim()) {
                valid = false;
                alert("Title is required.");
                title.focus();
            } else if (!date.value.trim()) {
                valid = false;
                alert("Date is required.");
                date.focus();
            } else if (!location.value.trim()) {
                valid = false;
                alert("Location is required.");
                location.focus();
            } else if (!description.value.trim()) {
                valid = false;
                alert("Description is required.");
                description.focus();
            }

            if (!valid) {
                event.preventDefault(); // Prevent form submission if validation fails
            }
        });
    }

    // Discussion form validation
    const discussionForm = document.querySelector("form.discussion-form");

    if (discussionForm) {
        discussionForm.addEventListener("submit", function (event) {
            let valid = true;
            const topic = document.getElementById("topic");
            const content = document.getElementById("content");
            const category = document.getElementById("category");

            // Simple validation checks
            if (!topic.value.trim()) {
                valid = false;
                alert("Topic is required.");
                topic.focus();
            } else if (!content.value.trim()) {
                valid = false;
                alert("Content is required.");
                content.focus();
            } else if (!category.value.trim()) {
                valid = false;
                alert("Category is required.");
                category.focus();
            }

            if (!valid) {
                event.preventDefault(); // Prevent form submission if validation fails
            }
        });
    }

    // Job post form validation
    const jobForm = document.querySelector("form.job-form");

    if (jobForm) {
        jobForm.addEventListener("submit", function (event) {
            let valid = true;
            const title = document.getElementById("title");
            const description = document.getElementById("description");
            const company = document.getElementById("company");
            const location = document.getElementById("location");

            // Simple validation checks
            if (!title.value.trim()) {
                valid = false;
                alert("Title is required.");
                title.focus();
            } else if (!description.value.trim()) {
                valid = false;
                alert("Description is required.");
                description.focus();
            } else if (!company.value.trim()) {
                valid = false;
                alert("Company is required.");
                company.focus();
            } else if (!location.value.trim()) {
                valid = false;
                alert("Location is required.");
                location.focus();
            }

            if (!valid) {
                event.preventDefault(); // Prevent form submission if validation fails
            }
        });
    }

    // Mentorship form validation
    const mentorshipForm = document.querySelector("form.mentorship-form");

    if (mentorshipForm) {
        mentorshipForm.addEventListener("submit", function (event) {
            let valid = true;
            const mentorName = document.getElementById("mentor_name");
            const menteeName = document.getElementById("mentee_name");
            const details = document.getElementById("details");
            const contactInfo = document.getElementById("contact_info");

            // Simple validation checks
            if (!mentorName.value.trim()) {
                valid = false;
                alert("Mentor name is required.");
                mentorName.focus();
            } else if (!menteeName.value.trim()) {
                valid = false;
                alert("Mentee name is required.");
                menteeName.focus();
            } else if (!details.value.trim()) {
                valid = false;
                alert("Details are required.");
                details.focus();
            } else if (!contactInfo.value.trim()) {
                valid = false;
                alert("Contact information is required.");
                contactInfo.focus();
            }

            if (!valid) {
                event.preventDefault(); // Prevent form submission if validation fails
            }
        });
    }

    // // Hide flash messages after 5 seconds
    // const flashes = document.querySelectorAll(".flash");
    // flashes.forEach(function (flash) {
    //     setTimeout(function () {
    //         flash.style.display = "none";
    //     }, 5000); // 5000 milliseconds = 5 seconds
    // });
});

document.addEventListener("DOMContentLoaded", function () {
    // Hide flash messages after 5 seconds
    const flashes = document.querySelectorAll(".alert");
    flashes.forEach(function (alert) {
        setTimeout(function () {
            alert.style.display = "none";
        }, 5000); // 5000 milliseconds = 5 seconds
    });
});


