// ==========================================================================
// CONFIGURATION: Set your deployed backend portal URL here (e.g. on Render/Railway)
// ==========================================================================
const PORTAL_BACKEND_URL = 'https://client-website-0pzy.onrender.com'; // CHANGE THIS after deploying your dynamic app!

// Helper function to resolve login/signup links between Local and Production
function getPortalLink(path) {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    return isLocal ? path : `${PORTAL_BACKEND_URL}${path}`;
}

document.addEventListener('DOMContentLoaded', () => {
    
    // Automatically rewrite local relative links to point to the production backend if hosted on GitHub Pages
    const links = document.querySelectorAll('a');
    links.forEach(link => {
        const href = link.getAttribute('href');
        if (href === '/login' || href === '/signup') {
            link.setAttribute('href', getPortalLink(href));
        }
    });
    
    // ==========================================================================
    // 1. MOBILE NAVBAR DRAWER TOGGLE
    // ==========================================================================
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('open');
            // Toggle hamburger icon between bars and times
            const icon = menuToggle.querySelector('i');
            if (icon) {
                if (navMenu.classList.contains('open')) {
                    icon.classList.remove('fa-bars');
                    icon.classList.add('fa-xmark');
                } else {
                    icon.classList.remove('fa-xmark');
                    icon.classList.add('fa-bars');
                }
            }
        });
        
        // Close menu when links are clicked on mobile
        const navLinks = navMenu.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('open');
                const icon = menuToggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-xmark');
                    icon.classList.add('fa-bars');
                }
            });
        });
    }

    // ==========================================================================
    // 2. NAVBAR SCROLL EFFECT
    // ==========================================================================
    const navbar = document.querySelector('.navbar');
    
    const handleScroll = () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    };
    
    window.addEventListener('scroll', handleScroll);
    // Initial check on load
    handleScroll();

    // ==========================================================================
    // 3. SHOWREEL VIDEO PLAYER INTERACTIVE SWAP
    // ==========================================================================
    const videoPlaceholder = document.getElementById('videoPlaceholder');
    const videoHolder = document.getElementById('videoHolder');
    
    if (videoPlaceholder && videoHolder) {
        videoPlaceholder.addEventListener('click', () => {
            videoPlaceholder.style.display = 'none';
            videoHolder.style.display = 'block';
            
            // Adjust iframe src to play immediately
            const iframe = videoHolder.querySelector('iframe');
            if (iframe) {
                const currentSrc = iframe.getAttribute('src');
                if (currentSrc && !currentSrc.includes('autoplay=1')) {
                    // Force autoplay
                    iframe.setAttribute('src', currentSrc.replace('autoplay=0', 'autoplay=1').replace('mute=1', 'mute=0'));
                }
            }
        });
    }

    // ==========================================================================
    // 4. PORTFOLIO FILTER SYSTEM
    // ==========================================================================
    const filterButtons = document.querySelectorAll('.filter-btn');
    const portfolioItems = document.querySelectorAll('.portfolio-item');
    
    if (filterButtons.length > 0 && portfolioItems.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                button.classList.add('active');
                
                const filterValue = button.getAttribute('data-filter');
                
                portfolioItems.forEach(item => {
                    const category = item.getAttribute('data-category');
                    
                    if (filterValue === 'all' || category === filterValue) {
                        item.style.display = 'block';
                        // Add fade-in transition effect
                        item.style.opacity = '0';
                        setTimeout(() => {
                            item.style.opacity = '1';
                            item.style.transition = 'opacity 0.4s ease';
                        }, 50);
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }

    // ==========================================================================
    // 5. ACTIVE MENU LINK ON SCROLL (Intersection Observer)
    // ==========================================================================
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.nav-link');
    
    const options = {
        root: null,
        threshold: 0.3, // Highlight when section is 30% visible
        rootMargin: '-80px 0px 0px 0px' // Offset navbar height
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                navLinks.forEach(link => {
                    const href = link.getAttribute('href');
                    if (href === `#${id}`) {
                        link.classList.add('active');
                    } else {
                        link.classList.remove('active');
                    }
                });
            }
        });
    }, options);
    
    sections.forEach(section => {
        observer.observe(section);
    });

    // ==========================================================================
    // 6. CONTACT FORM SIMULATOR
    // ==========================================================================
    const contactForm = document.getElementById('contactForm');
    const formStatus = document.getElementById('formStatus');
    const submitBtn = document.getElementById('submitBtn');
    
    if (contactForm && formStatus && submitBtn) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Disable button
            submitBtn.disabled = true;
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = 'Sending... <i class="fa-solid fa-spinner fa-spin"></i>';
            
            // Get values
            const name = document.getElementById('formName').value;
            const email = document.getElementById('formEmail').value;
            const service = document.getElementById('formService').value;
            const message = document.getElementById('formMessage').value;
            
            // Simulate API request (1.5 seconds delay)
            setTimeout(() => {
                // Visual response
                formStatus.className = 'form-status status-success animate-fade-in';
                formStatus.innerHTML = `<i class="fa-solid fa-circle-check"></i> Thank you, ${name}! Your inquiry has been sent. I will get back to you shortly.`;
                
                // Reset form
                contactForm.reset();
                
                // Re-enable button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                
                // Clear status after 6 seconds
                setTimeout(() => {
                    formStatus.innerHTML = '';
                    formStatus.className = 'form-status';
                }, 6000);
                
            }, 1500);
        });
    }

});
