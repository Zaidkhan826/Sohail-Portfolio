// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener("click", function(e){
        e.preventDefault();

        const target = document.querySelector(this.getAttribute("href"));

        if(target){
            target.scrollIntoView({
                behavior: "smooth"
            });
        }
    });
});


// Navbar background on scroll
window.addEventListener("scroll", () => {

    const navbar = document.querySelector(".navbar");

    if(navbar){
        if(window.scrollY > 50){
            navbar.style.background = "rgba(0,0,0,0.95)";
            navbar.style.boxShadow = "0 5px 20px rgba(108,99,255,0.3)";
        }else{
            navbar.style.background = "rgba(255,255,255,.05)";
            navbar.style.boxShadow = "none";
        }
    }

});


// Fade animation when sections appear
const sections = document.querySelectorAll(".section");

const observer = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if(entry.isIntersecting){
            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0)";
        }

    });

}, {
    threshold: 0.2
});

sections.forEach(section => {
    section.style.opacity = "0";
    section.style.transform = "translateY(20px)";
    section.style.transition = "all 0.6s ease";

    observer.observe(section);
});


// Scroll to top button
let scrollBtn = document.getElementById("scrollBtn");

window.addEventListener("scroll", () => {
    if(!scrollBtn) return;

    if(document.documentElement.scrollTop > 200){
        scrollBtn.style.display = "block";
    } else {
        scrollBtn.style.display = "none";
    }
});

function scrollToTop(){
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}